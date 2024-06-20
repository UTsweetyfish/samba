#!/usr/bin/env python3

#
# Unix SMB/CIFS implementation.
#
# HRESULT Error definitions
#
# Copyright (C) Noel Power <noel.power@suse.com> 2014
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


import sys
from gen_error_common import parseErrorDescriptions

def write_license(out_file):
    out_file.write("/*\n")
    out_file.write(" * Unix SMB/CIFS implementation.\n")
    out_file.write(" *\n")
    out_file.write(" * HRESULT Error definitions\n")
    out_file.write(" *\n")
    out_file.write(" * Copyright (C) Noel Power <noel.power@suse.com> 2014\n")
    out_file.write(" *\n")
    out_file.write(" * This program is free software; you can redistribute it and/or modify\n")
    out_file.write(" * it under the terms of the GNU General Public License as published by\n")
    out_file.write(" * the Free Software Foundation; either version 3 of the License, or\n")
    out_file.write(" * (at your option) any later version.\n")
    out_file.write(" *\n")
    out_file.write(" * This program is distributed in the hope that it will be useful,\n")
    out_file.write(" * but WITHOUT ANY WARRANTY; without even the implied warranty of\n")
    out_file.write(" * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n")
    out_file.write(" * GNU General Public License for more details.\n")
    out_file.write(" *\n")
    out_file.write(" * You should have received a copy of the GNU General Public License\n")
    out_file.write(" * along with this program.  If not, see <http://www.gnu.org/licenses/>.\n")
    out_file.write(" */\n")
    out_file.write("\n")

def generateHeaderFile(out_file, errors):
    write_license(out_file)
    out_file.write("#ifndef _HRESULT_H_\n")
    out_file.write("#define _HRESULT_H_\n\n")
    macro_magic = "#if defined(HAVE_IMMEDIATE_STRUCTURES)\n"
    macro_magic += "typedef struct {uint32_t h;} HRESULT;\n"
    macro_magic += "#define HRES_ERROR(x) ((HRESULT) { x })\n"
    macro_magic += "#define HRES_ERROR_V(x) ((x).h)\n"
    macro_magic += "#else\n"
    macro_magic += "typedef uint32_t HRESULT;\n"
    macro_magic += "#define HRES_ERROR(x) (x)\n"
    macro_magic += "#define HRES_ERROR_V(x) (x)\n"
    macro_magic += "#endif\n"
    macro_magic += "\n"
    macro_magic += "#define HRES_IS_OK(x) (HRES_ERROR_V(x) == 0)\n"
    macro_magic += "#define HRES_IS_EQUAL(x,y) (HRES_ERROR_V(x) == HRES_ERROR_V(y))\n"

    out_file.write(macro_magic)
    out_file.write("\n\n")
    out_file.write("/*\n")
    out_file.write(" * The following error codes are autogenerated from [MS-ERREF]\n")
    out_file.write(" * see http://msdn.microsoft.com/en-us/library/cc704587.aspx\n")
    out_file.write(" */\n")
    out_file.write("\n")

    for err in errors:
        line = "#define {0:49} HRES_ERROR(0x{1:08X})\n".format(err.err_define ,err.err_code)
        out_file.write(line)
    out_file.write("\nconst char *hresult_errstr_const(HRESULT err_code);\n")
    out_file.write("\nconst char *hresult_errstr(HRESULT err_code);\n")
    out_file.write("\n#define FACILITY_WIN32 0x0007\n")
    out_file.write("#define WIN32_FROM_HRESULT(x) (HRES_ERROR_V(x) == 0 ? HRES_ERROR_V(x) : ~((FACILITY_WIN32 << 16) | 0x80000000) & HRES_ERROR_V(x))\n")
    out_file.write("#define HRESULT_IS_LIKELY_WERR(x) ((HRES_ERROR_V(x) & 0xFFFF0000) == 0x80070000)\n")
    out_file.write("#define HRESULT_FROM_WERROR(x) (HRES_ERROR(0x80070000 | W_ERROR_V(x)))\n")
    out_file.write("\n\n\n#endif /*_HRESULT_H_*/")


def generateSourceFile(out_file, errors):
    write_license(out_file)
    out_file.write("#include \"includes.h\"\n")
    out_file.write("#include \"hresult.h\"\n")
    out_file.write("/*\n")
    out_file.write(" * The following error codes and descriptions are autogenerated from [MS-ERREF]\n")
    out_file.write(" * see http://msdn.microsoft.com/en-us/library/cc704587.aspx\n")
    out_file.write(" */\n")
    out_file.write("\n")
    out_file.write("const char *hresult_errstr_const(HRESULT err_code)\n")
    out_file.write("{\n")
    out_file.write("	const char *result = NULL;\n")
    out_file.write("\n")
    out_file.write("	switch (HRES_ERROR_V(err_code)) {\n")
    for err in errors:
        out_file.write(f'            case 0x{err.err_code:X}:\n')
        out_file.write(f'                result = \"{err.err_define}\";\n')
        out_file.write(f'                break;\n')
    out_file.write("	}\n")
    out_file.write("\n")
    out_file.write("	/* convert & check win32 error space? */\n")
    out_file.write("	if (result == NULL && HRESULT_IS_LIKELY_WERR(err_code)) {\n")
    out_file.write("		WERROR wErr = W_ERROR(WIN32_FROM_HRESULT(err_code));\n")
    out_file.write("		result = get_friendly_werror_msg(wErr);\n")
    out_file.write("	}\n")
    out_file.write("	return result;\n")
    out_file.write("}\n")
    out_file.write("\n")
    out_file.write("const char *hresult_errstr(HRESULT err_code)\n")
    out_file.write("{\n")
    out_file.write("	static char msg[22];\n")
    out_file.write("\n")
    out_file.write("	switch (HRES_ERROR_V(err_code)) {\n")
    for err in errors:
        out_file.write(f'            case 0x{err.err_code:X}:\n')
        out_file.write(f'                return \"{err.err_string}\";\n')
        out_file.write(f'                break;\n')
    out_file.write("	}\n")
    out_file.write("	snprintf(msg, sizeof(msg), \"HRES code 0x%08x\", HRES_ERROR_V(err_code));\n")
    out_file.write("	return msg;\n")
    out_file.write("}\n")

def generatePythonFile(out_file, errors):
    out_file.write("/*\n")
    out_file.write(" * Errors generated from\n")
    out_file.write(" * [MS-ERREF] http://msdn.microsoft.com/en-us/library/cc704587.aspx\n")
    out_file.write(" */\n")
    out_file.write("#include \"lib/replace/system/python.h\"\n")
    out_file.write("#include \"python/py3compat.h\"\n")
    out_file.write("#include \"includes.h\"\n\n")
    out_file.write("static struct PyModuleDef moduledef = {\n")
    out_file.write("\tPyModuleDef_HEAD_INIT,\n")
    out_file.write("\t.m_name = \"hresult\",\n")
    out_file.write("\t.m_doc = \"HRESULT defines\",\n")
    out_file.write("\t.m_size = -1,\n")
    out_file.write("\t};\n\n")
    out_file.write("MODULE_INIT_FUNC(hresult)\n")
    out_file.write("{\n")
    out_file.write("\tPyObject *m = NULL;\n")
    out_file.write("\tPyObject *py_obj = NULL;\n")
    out_file.write("\tint ret;\n\n")
    out_file.write("\tm = PyModule_Create(&moduledef);\n")
    out_file.write("\tif (m == NULL) {\n")
    out_file.write("\t\treturn NULL;\n")
    out_file.write("\t}\n\n")
    for err in errors:
        out_file.write(f"\tpy_obj = PyLong_FromUnsignedLongLong(HRES_ERROR_V({err.err_define}));\n")
        out_file.write(f"\tret = PyModule_AddObject(m, \"{err.err_define}\", py_obj);\n")
        out_file.write("\tif (ret) {\n")
        out_file.write("\t\tPy_XDECREF(py_obj);\n")
        out_file.write("\t\tPy_DECREF(m);\n")
        out_file.write("\t\treturn NULL;\n")
        out_file.write("\t}\n")
    out_file.write("\n")
    out_file.write("\treturn m;\n")
    out_file.write("}\n")

def transformErrorName(error_name):
    return "HRES_" + error_name

# Very simple script to generate files hresult.c & hresult.h
# This script takes four inputs:
# [1]: The name of the text file which is the content of an HTML table
#      (such as that found at https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/705fb797-2175-4a90-b5a3-3918024b10b8)
#      copied and pasted.
# [2]: The name of the output generated header file with HResult #defines
# [3]: The name of the output generated source file with C arrays
# [4]: The name of the output generated python file

def main ():
    input_file1 = None

    if len(sys.argv) == 5:
        input_file1 =  sys.argv[1]
        gen_headerfile_name = sys.argv[2]
        gen_sourcefile_name = sys.argv[3]
        gen_pythonfile_name = sys.argv[4]
    else:
        print("usage: %s winerrorfile headerfile sourcefile pythonfile"%(sys.argv[0]))
        sys.exit()

    # read in the data
    with open(input_file1) as file_contents:
        errors = parseErrorDescriptions(file_contents, False, transformErrorName)

    print(f"writing new header file: {gen_headerfile_name}")
    with open(gen_headerfile_name,"w") as out_file:
        generateHeaderFile(out_file, errors)
    print(f"writing new source file: {gen_sourcefile_name}")
    with open(gen_sourcefile_name,"w") as out_file:
        generateSourceFile(out_file, errors)
    print(f"writing new python file: {gen_pythonfile_name}")
    with open(gen_pythonfile_name,"w") as out_file:
        generatePythonFile(out_file, errors)

if __name__ == '__main__':

    main()
