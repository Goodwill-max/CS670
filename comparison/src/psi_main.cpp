#include <libPSI/PSI/Kkrt/KkrtPsiReceiver.h>
#include <libPSI/PSI/Kkrt/KkrtPsiSender.h>
#include <libOTe/NChooseOne/Kkrt/KkrtNcoOtReceiver.h>
#include <libOTe/NChooseOne/Kkrt/KkrtNcoOtSender.h>
#include <cryptoTools/Crypto/RandomOracle.h>
#include <cryptoTools/Crypto/PRNG.h>
#include <cryptoTools/Network/Endpoint.h>
#include <cryptoTools/Network/IOService.h>
#include <algorithm>
#include <array>
#include <cstring>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <map>
#include <queue>
#include <set>
#include <stdexcept>
#include <vector>
using namespace osuCrypto;
using Words = std::vector<block>;
block digest(const std::string& s) {
    RandomOracle h(16); h.Update(reinterpret_cast<const u8*>(s.data()), s.size());
    block b; h.Final(reinterpret_cast<u8*>(&b)); return b;
}
std::vector<std::string> load(const std::string& path) {
    std::ifstream f(path); if(!f) throw std::runtime_error("Cannot read " + path);
    std::set<std::string> unique; std::string s;
    while(std::getline(f,s)) { if(!s.empty() && s.back()=='\r') s.pop_back(); if(!s.empty()) unique.insert(s); }
    if(unique.empty()) throw std::runtime_error("Input must contain at least one contact");
    return {unique.begin(),unique.end()};
}
Words encode(const std::vector<std::string>& strings) {
    Words out; for(auto& s:strings) out.push_back(digest("pir-psi/contact/v1/"+s)); return out;
}
void sendNum(Channel& c,u64 n){c.asyncSendCopy(reinterpret_cast<u8*>(&n),8);}
u64 recvNum(Channel& c){u64 n;c.recv(reinterpret_cast<u8*>(&n),8);return n;}
void metrics(const std::string& role, Channel& c, Channel* extra=nullptr) {
    if(!std::getenv("PIR_PSI_METRICS"))return;
    std::cerr<<"METRICS {\"role\":\""<<role<<"\",\"sent\":"<<c.getTotalDataSent()
             <<",\"received\":"<<c.getTotalDataRecv()<<",\"extra_sent\":"<<(extra?extra->getTotalDataSent():0)
             <<",\"extra_received\":"<<(extra?extra->getTotalDataRecv():0)<<"}\n";
}

int main(int argc,char**argv) try {
    if(argc<3)throw std::runtime_error("Usage: kkrt_psi psi-server|psi-client contacts.txt [port]");
    std::string role=argv[1];
    if(role!="psi-server" && role!="psi-client")throw std::runtime_error("Unknown role");
    auto strings=load(argv[2]);auto items=encode(strings);
    int port=argc>3?std::stoi(argv[3]):18080;
    if(port<1024 || port>65532)throw std::runtime_error("Invalid port");
    PRNG random(sysRandomSeed());IOService ios;
    auto addr=[&](int offset){return "127.0.0.1:"+std::to_string(port+offset);};
    // Direct two-party KKRT baseline: same encoder, security parameter and OTs.
    if(role=="psi-server" || role=="psi-client") {
        bool server=role=="psi-server";
        Endpoint ep(ios,addr(0),server?EpMode::Server:EpMode::Client,"direct-psi");
        auto c=ep.addChannel("data");sendNum(c,items.size());auto peerSize=recvNum(c);
        if(peerSize==0||peerSize>1000000)throw std::runtime_error("Invalid peer size");
        if(server){KkrtNcoOtSender ot;KkrtPsiSender sender;
            sender.init(items.size(),peerSize,40,c,ot,random.get<block>());sender.sendInput(items,c);
        }else{KkrtNcoOtReceiver ot;KkrtPsiReceiver receiver;
            receiver.init(peerSize,items.size(),40,c,ot,random.get<block>());receiver.sendInput(items,c);
            std::set<u64> matched(receiver.mIntersection.begin(),receiver.mIntersection.end());
            for(auto idx:matched)std::cout<<strings.at(idx)<<"\n";
        }
        c.close();metrics(role,c);return 0;
    }
}catch(const std::exception& e){std::cerr<<"Error: "<<e.what()<<"\n";return 1;}
