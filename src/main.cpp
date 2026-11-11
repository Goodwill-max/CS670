// Research implementation of the unbinned, single-entry-block protocol,
// paper Sections 2.3, 3.1-3.3. Cryptographic primitives are upstream libPSI.
#include <libPSI/PIR/BgiPirClient.h>
#include <libPSI/PIR/BgiPirServer.h>
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
// Three domain-separated public random-oracle hash functions.
u64 location(block x, block salt, u64 j, u64 size) {
    RandomOracle h(16); h.Update(reinterpret_cast<u8*>(&x),16);
    h.Update(reinterpret_cast<u8*>(&salt),16); h.Update(reinterpret_cast<u8*>(&j),8);
    std::array<u8,16> out; h.Final(out.data()); u64 v; std::memcpy(&v,out.data(),8); return v%size;
}
u64 tableSize(u64 n) { u64 m=128; while(m<2*n) m*=2; return m; }
// Deterministic augmenting-path cuckoo insertion: both replicas construct the
// same table. Failure aborts instead of silently dropping an entry or using a stash.
Words cuckoo(const Words& items, block salt, u64 m) {
    std::vector<long long> slots(m,-1);
    for(u64 i=0;i<items.size();++i) {
        std::vector<long long> parent(m,-2); std::queue<u64> q;
        for(u64 j=0;j<3;++j) {auto p=location(items[i],salt,j,m); if(parent[p]==-2){parent[p]=-1;q.push(p);}}
        long long end=-1;
        while(!q.empty()) {auto p=q.front();q.pop(); if(slots[p]<0){end=p;break;}
            for(u64 j=0;j<3;++j) {auto next=location(items[slots[p]],salt,j,m);
                if(parent[next]==-2){parent[next]=p;q.push(next);}}
        }
        if(end<0) throw std::runtime_error("Cuckoo insertion failed; rerun with a fresh salt");
        while(parent[end]!=-1) { slots[end]=slots[parent[end]];end=parent[end]; }
        slots[end]=i;
    }
    Words table(m,ZeroBlock); for(u64 i=0;i<m;++i) if(slots[i]>=0) table[i]=items[slots[i]];
    return table;
}
void sendBlock(Channel& c, block b){ c.asyncSendCopy(reinterpret_cast<u8*>(&b),16); }
block recvBlock(Channel& c){block b;c.recv(reinterpret_cast<u8*>(&b),16);return b;}
void sendNum(Channel& c,u64 n){c.asyncSendCopy(reinterpret_cast<u8*>(&n),8);}
u64 recvNum(Channel& c){u64 n;c.recv(reinterpret_cast<u8*>(&n),8);return n;}
u64 depth(u64 m){u64 d=0;while((u64(128)<<d)<m)++d;return d;}
Words readKey(Channel& c,u64 d) {Words k; c.recv(k); if(k.size()!=d+1)throw std::runtime_error("Bad DPF key length");return k;}
Words readGroup(Channel& c){Words g;c.recv(g);if(g.size()!=1)throw std::runtime_error("Bad DPF group length");return g;}
int selftest() {
    PRNG random(sysRandomSeed());
    for(u64 m:{u64(128),u64(512),u64(2048)}) {
        Words data(m);for(auto& x:data)x=random.get<block>();
        for(u64 idx:{u64(0),u64(1),m/2,m-1}) {
            auto d=depth(m);Words k0(d+1),k1(d+1),g0(1),g1(1);
            BgiPirClient::keyGen(idx,random.get<block>(),k0,g0,k1,g1);
            auto result=BgiPirServer::fullDomain(data,k0,g0)^BgiPirServer::fullDomain(data,k1,g1);
            if(std::memcmp(&result,&data[idx],16))throw std::runtime_error("DPF/PIR reconstruction failed");
            for(u64 j=0;j<m;++j)
                if((BgiPirServer::evalOne(j,k0,g0)^BgiPirServer::evalOne(j,k1,g1)) != (j==idx))
                    throw std::runtime_error("DPF point-function invariant failed");
        }
    }
    Words items(256);for(auto& x:items)x=random.get<block>();auto salt=random.get<block>();
    auto table=cuckoo(items,salt,tableSize(items.size()));
    for(auto x:items){bool found=false;for(u64 j=0;j<3;++j){auto p=location(x,salt,j,table.size());
        found |= std::memcmp(&x,&table[p],16)==0;}if(!found)throw std::runtime_error("Cuckoo item missing");}
    std::cout<<"PASS: DPF point functions, PIR reconstruction, cuckoo placement\n";return 0;
}
int main(int argc,char**argv) try {
    if(argc==2 && std::string(argv[1])=="selftest")return selftest();
    if(argc<3){std::cerr<<"Usage: contact_discovery server0|server1|client contacts.txt [base-port=18080]\n";return 2;}
    std::string role=argv[1]; if(role!="server0"&&role!="server1"&&role!="client")throw std::runtime_error("Unknown role");
    auto strings=load(argv[2]);auto items=encode(strings);
    int port=argc>3?std::stoi(argv[3]):18080;
    if(port<1024||port>65532)throw std::runtime_error("Bad port");
    PRNG random(sysRandomSeed()); IOService ios;
    auto addr=[&](int offset){return "127.0.0.1:"+std::to_string(port+offset);};
    if(role=="client") {
        Endpoint e0(ios,addr(0),EpMode::Client,"c0"), e1(ios,addr(1),EpMode::Client,"c1");
        auto c0=e0.addChannel("data"),c1=e1.addChannel("data");
        auto m=recvNum(c0);block salt=recvBlock(c0);
        if(m<128 || (m&(m-1)) || m>(u64(1)<<30))throw std::runtime_error("Invalid table size");
        sendNum(c0,items.size()); sendNum(c1,items.size());
        u64 d=depth(m);Words psi; psi.reserve(items.size()*3);
        for(auto x:items) {
            Words masks(3); for(auto& r:masks)r=random.get<block>();
            c1.asyncSendCopy(masks);
            for(u64 j=0;j<3;++j){
                Words k0(d+1),k1(d+1),g0(1),g1(1);
                BgiPirClient::keyGen(location(x,salt,j,m),random.get<block>(),k0,g0,k1,g1);
                c0.asyncSend(std::move(k0));c0.asyncSend(std::move(g0));
                c1.asyncSend(std::move(k1));c1.asyncSend(std::move(g1));
                psi.push_back(x^masks[j]);
            }
        }
        KkrtNcoOtReceiver ot;KkrtPsiReceiver receiver;
        receiver.init(psi.size(),psi.size(),40,c0,ot,random.get<block>());
        receiver.sendInput(psi,c0);
        std::set<u64> matches;for(auto idx:receiver.mIntersection)matches.insert(idx/3);
        for(auto idx:matches)std::cout<<strings.at(idx)<<"\n";
        c0.close();c1.close();
        return 0;
    }
    bool first=role=="server0";
    Endpoint ec(ios,addr(first?0:1),EpMode::Server,first?"c0":"c1");
    Endpoint es(ios,addr(2),first?EpMode::Server:EpMode::Client,"replicas");
    auto c=ec.addChannel("data"),other=es.addChannel("data");
    u64 m=tableSize(items.size());block salt;
    // Check replicated database agreement without sending the raw contacts.
    std::string joined;for(auto& s:strings){joined+=std::to_string(s.size())+":"+s;}
    sendBlock(other,digest(joined));auto peer=recvBlock(other);
    block own=digest(joined);if(std::memcmp(&own,&peer,16))throw std::runtime_error("Server databases differ");
    if(first){salt=random.get<block>();sendBlock(other,salt);sendNum(c,m);sendBlock(c,salt);}
    else salt=recvBlock(other);
    auto table=cuckoo(items,salt,m);u64 n=recvNum(c);
    if(n==0||n>1000000)throw std::runtime_error("Invalid client size");
    sendNum(other,n);if(recvNum(other)!=n)throw std::runtime_error("Client sizes differ");
    Words psi;psi.reserve(3*n);auto d=depth(m);
    for(u64 i=0;i<n;++i){
        Words masks;
        if(!first){c.recv(masks);if(masks.size()!=3)throw std::runtime_error("Invalid masks");std::shuffle(masks.begin(),masks.end(),random);}
        for(u64 j=0;j<3;++j){auto k=readKey(c,d);auto g=readGroup(c);
            block v=BgiPirServer::fullDomain(table,k,g);
            if(first)psi.push_back(v^recvBlock(other));else sendBlock(other,v^masks[j]);
        }
    }
    if(first){KkrtNcoOtSender ot;KkrtPsiSender sender;
        sender.init(psi.size(),psi.size(),40,c,ot,random.get<block>());sender.sendInput(psi,c);}
    c.close();other.close();
    return 0;
}catch(const std::exception& e){std::cerr<<"Error: "<<e.what()<<"\n";return 1;}
