cmake_minimum_required(VERSION 2.8)

include(RezBuild)

file(GLOB_RECURSE py_files "src/*.py")
rez_install_python(
    py
    FILES ${py_files}
    DESTINATION .
)