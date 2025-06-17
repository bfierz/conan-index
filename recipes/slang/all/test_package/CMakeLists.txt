cmake_minimum_required(VERSION 3.15)

project(test_package LANGUAGES CXX)

find_program(slangc slangc REQUIRED)

if(NOT slangc)
    message(FATAL_ERROR "slang not found!")
endif()

execute_process(
    COMMAND ${slangc} -v
    OUTPUT_VARIABLE slang_output
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_VARIABLE slang_error
    ERROR_STRIP_TRAILING_WHITESPACE
)
message(STATUS "Found SLANG: ${slangc} (version: ${slang_output}${slang_error})")
