from conans import ConanFile, CMake, python_requires, tools
from conans.errors import ConanInvalidConfiguration

from pathlib import Path
import networkx as nx

import re


class LLVMConan(ConanFile):
    name = 'llvm'
    version = '9.0.1'
    license = 'Apache-2'
    description = 'A collection of modular compiler and toolchain technologies.'
    homepage = 'https://llvm.org/'
    url = 'https://github.com/llvm/llvm-project'

    settings = ('os', 'arch', 'compiler', 'build_type')
    options = {
        'shared': [True, False],
        'fPIC': [True, False],
        'dylib_library': [True, False],
        'dylib_components': 'ANY',
        'targets': 'ANY',
        'exceptions': [True, False],
        'rtti': [True, False],
        'threads': [True, False],
        'lto': ['On', 'Off', 'Full', 'Thin'],
        'static_stdlib': [True, False],
        'unwind_tables': [True, False],
        'expensive_checks': [True, False],
        'use_perf': [True, False],
        'with_zlib': [True, False],
        'with_xml2': [True, False],
        'with_ffi': [True, False]
    }
    default_options = {
        'shared': False,
        'fPIC': True,
        'dylib_library': False,
        'dylib_components': 'all',
        'targets': 'X86',
        'exceptions': True,
        'rtti': True,
        'threads': True,
        'lto': 'Off',
        'static_stdlib': False,
        'unwind_tables': True,
        'expensive_checks': False,
        'use_perf': False,
        'with_zlib': True,
        'with_xml2': True,
        'with_ffi': False
    }

    exports_sources = ['CMakeLists.txt', 'iconv.patch']
    generators = 'cmake'
    no_copy_source = True

    _source_subfolder = 'source'

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC
            del self.options.dylib_library
            del self.options.dylib_components

    def requirements(self):
        if self.options.with_zlib:
            self.requires('zlib/1.2.11')
        if self.options.with_xml2:
            self.requires('libxml2/2.9.10')
        if self.options.with_ffi:
            self.requires('libffi/3.3')

    def configure(self):
        if self.settings.os != 'Windows' and self.options.shared:
            self.options.dylib_library = False
        if self.options.exceptions:
            self.options.rtti = True

    def source(self):
        url = f'{self.url}/releases/download/llvmorg-{self.version}/' \
              f'llvm-{self.version}.src.tar.xz'
        filename = f'llvm-{self.version}.tar.xz'

        tools.download(url, filename, verify=False)
        tools.unzip(filename, destination=self._source_subfolder)
        Path(filename).unlink()

        source_path = Path(self._source_subfolder)
        for item in source_path.joinpath(f'llvm-{self.version}.src').iterdir():
            item.rename(str(source_path.joinpath(item.name).resolve()))
        source_path.joinpath(f'llvm-{self.version}.src').rmdir()

        tools.patch(base_path=self._source_subfolder, patch_file='iconv.patch')

    def build(self):
        build_system = CMake(self)

        build_system.definitions['CMAKE_SKIP_RPATH'] = True
        build_system.definitions['LLVM_TARGETS_TO_BUILD'] = self.options.targets
        build_system.definitions['LLVM_TARGET_ARCH'] = 'host'
        if self.settings.os != 'Windows':
            build_system.definitions['LLVM_ENABLE_PIC'] = self.options.fPIC
            build_system.definitions['LLVM_LINK_LLVM_DYLIB'] = \
                self.options.dylib_library
            build_system.definitions['LLVM_DYLIB_COMPONENTS'] = \
                self.options.dylib_components

        build_system.definitions['LLVM_ABI_BREAKING_CHECKS'] = 'WITH_ASSERTS'
        build_system.definitions['LLVM_ENABLE_WARNINGS'] = True
        build_system.definitions['LLVM_ENABLE_PEDANTIC'] = True
        build_system.definitions['LLVM_ENABLE_WERROR'] = False
        build_system.definitions['LLVM_ENABLE_LIBCXX'] = \
            'clang' in str(self.settings.compiler)

        build_system.definitions['LLVM_USE_RELATIVE_PATHS_IN_DEBUG_INFO'] = True
        build_system.definitions['LLVM_TEMPORARILY_ALLOW_OLD_TOOLCHAIN'] = False
        build_system.definitions['LLVM_BUILD_INSTRUMENTED_COVERAGE'] = False
        build_system.definitions['LLVM_OPTIMIZED_TABLEGEN'] = True
        build_system.definitions['LLVM_REVERSE_ITERATION'] = False
        build_system.definitions['LLVM_ENABLE_BINDINGS'] = False
        build_system.definitions['LLVM_CCACHE_BUILD'] = False

        build_system.definitions['LLVM_INCLUDE_TOOLS'] = True
        build_system.definitions['LLVM_INCLUDE_EXAMPLES'] = False
        build_system.definitions['LLVM_INCLUDE_TESTS'] = False
        build_system.definitions['LLVM_INCLUDE_BENCHMARKS'] = False
        build_system.definitions['LLVM_APPEND_VC_REV'] = False
        build_system.definitions['LLVM_BUILD_DOCS'] = False
        build_system.definitions['LLVM_ENABLE_IDE'] = False

        build_system.definitions['LLVM_ENABLE_EH'] = self.options.exceptions
        build_system.definitions['LLVM_ENABLE_RTTI'] = self.options.rtti
        build_system.definitions['LLVM_ENABLE_THREADS'] = self.options.threads
        build_system.definitions['LLVM_ENABLE_LTO'] = self.options.lto
        build_system.definitions['LLVM_STATIC_LINK_CXX_STDLIB'] = \
            self.options.static_stdlib
        build_system.definitions['LLVM_ENABLE_UNWIND_TABLES'] = \
            self.options.unwind_tables
        build_system.definitions['LLVM_ENABLE_EXPENSIVE_CHECKS'] = \
            self.options.expensive_checks
        build_system.definitions['LLVM_ENABLE_ASSERTIONS'] = \
            self.settings.build_type == 'Debug'

        build_system.definitions['LLVM_USE_NEWPM'] = False
        build_system.definitions['LLVM_USE_OPROFILE'] = False
        build_system.definitions['LLVM_USE_PERF'] = self.options.use_perf

        build_system.definitions['LLVM_ENABLE_Z3_SOLVER'] = False
        build_system.definitions['LLVM_ENABLE_LIBPFM'] = False
        build_system.definitions['LLVM_ENABLE_LIBEDIT'] = False
        build_system.definitions['LLVM_ENABLE_ZLIB'] = self.options.with_zlib
        build_system.definitions['LLVM_ENABLE_LIBXML2'] = self.options.with_xml2
        build_system.definitions['LLVM_ENABLE_FFI'] = self.options.with_ffi
        if self.options.with_ffi:
            build_system.definitions['FFI_INCLUDE_DIR'] = \
                self.deps_cpp_info['libffi'].include_paths[0]
            build_system.definitions['FFI_LIBRARY_DIR'] = \
                self.deps_cpp_info['libffi'].lib_paths[0]

        build_system.configure()
        build_system.build()

    def package(self):
        build_system = CMake(self)
        build_system.install(build_dir='.')

        self.copy('LICENSE.TXT', dst='licenses', src=self._source_subfolder)

    def package_info(self):
        lib_regex = re.compile(
            r'add_library\((\w+?)\s.*?\)'
            r'(?:(?:#|\w|\s|\()+?'
            r'INTERFACE_LINK_LIBRARIES\s\"((?:;|/|\.|\w)+?)\"'
            r'(?:.|\n)*?\))?'
        )
        exports_file = 'LLVMExports.cmake'
        exports_path = Path('lib').joinpath('cmake', 'llvm', exports_file)

        exports = tools.load(str(exports_path.resolve()))
        exports = exports.replace('\$<LINK_ONLY:', '')
        exports = exports.replace('>', '')

        graph = nx.DiGraph()
        for match in re.finditer(lib_regex, exports):
            lib, deps = match.groups()
            if lib.startswith('LLVM'):
                for dep in deps.split(';') if deps is not None else []:
                    if dep.startswith('LLVM'):
                        graph.add_edge(lib, dep)
            else:
                graph.add_node(lib)

        libs = list(nx.lexicographical_topological_sort(graph))
        # components = {}
        # for node in graph.nodes:
        #     components[node] = sorted(
        #         nx.descendants(graph, node),
        #         key=lambda lib: libs.index(lib)
        #     )
        self.cpp_info.libs = libs
