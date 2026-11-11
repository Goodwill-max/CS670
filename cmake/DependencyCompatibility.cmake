# Runs before dependency project() calls, including newly cloned coproto.
# The legacy JFrog URL returns HTML. Preserve the original archive SHA256 check.
get_filename_component(CONTACT_ROOT "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
set(CONTACT_BOOST_SCRIPT "${CONTACT_ROOT}/vendor/libPSI/out/libOTe/out/coproto/thirdparty/getBoost.cmake")
if(EXISTS "${CONTACT_BOOST_SCRIPT}")
  file(READ "${CONTACT_BOOST_SCRIPT}" CONTACT_BOOST_TEXT)
  string(REPLACE "https://boostorg.jfrog.io/artifactory/main/release/" "https://archives.boost.io/release/" CONTACT_BOOST_FIXED "${CONTACT_BOOST_TEXT}")
  if(NOT CONTACT_BOOST_TEXT STREQUAL CONTACT_BOOST_FIXED)
    file(WRITE "${CONTACT_BOOST_SCRIPT}" "${CONTACT_BOOST_FIXED}")
  endif()
endif()
