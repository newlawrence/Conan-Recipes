from conans.errors import ConanInvalidConfiguration
from conans import ConanFile, CMake, tools

from pathlib import Path

import json
import time
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
        'components': 'ANY',
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
        'components': 'all',
        'targets': 'all',
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

    exports_sources = ['CMakeLists.txt', 'patches/*']
    generators = 'cmake'
    no_copy_source = True

    _source_subfolder = 'source'

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC
            del self.options.components
            del self.options.with_zlib
            del self.options.with_xml2
            del self.options.with_ffi

    def requirements(self):
        if self.options.get_safe('with_zlib', False):
            self.requires('zlib/1.2.11')
        if self.options.get_safe('with_xml2', False):
            self.requires('libxml2/2.9.10')
        if self.options.get_safe('with_ffi', False):
            self.requires('libffi/3.3')

    def configure(self):
        if self.settings.os == 'Windows' and self.options.shared:
            raise ConanInvalidConfiguration('build as shared lib not supported')
        if self.options.exceptions and not self.options.rtti:
            raise ConanInvalidConfiguration('exceptions require rtti support')

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

        tools.patch(
            base_path=self._source_subfolder,
            patch_file=str(Path('patches').joinpath('cmake.patch').resolve())
        )

    def build(self):
        build_system = CMake(self)

        build_system.definitions['BUILD_SHARED_LIBS'] = False
        build_system.definitions['CMAKE_SKIP_RPATH'] = True

        build_system.definitions['LLVM_TARGETS_TO_BUILD'] = self.options.targets
        build_system.definitions['LLVM_TARGET_ARCH'] = 'host'
        build_system.definitions['LLVM_BUILD_LLVM_DYLIB'] = \
            self.options.shared
        build_system.definitions['LLVM_ENABLE_PIC'] = \
            self.options.get_safe('fPIC', default=False)
        build_system.definitions['LLVM_DYLIB_COMPONENTS'] = \
            self.options.get_safe('components', default='all')

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

        build_system.definitions['LLVM_ENABLE_ZLIB'] = \
            self.options.get_safe('with_zlib', False)
        build_system.definitions['LLVM_ENABLE_LIBXML2'] = \
            self.options.get_safe('with_xml2', False)
        build_system.definitions['LLVM_ENABLE_FFI'] = \
            self.options.get_safe('with_ffi', False)
        if self.options.get_safe('with_ffi', False):
            build_system.definitions['FFI_INCLUDE_DIR'] = \
                self.deps_cpp_info['libffi'].include_paths[0]
            build_system.definitions['FFI_LIBRARY_DIR'] = \
                self.deps_cpp_info['libffi'].lib_paths[0]

        build_system.configure()
        build_system.build()

    def package(self):
        self.copy('LICENSE.TXT', dst='licenses', src=self._source_subfolder)
        package_path = Path(self.package_folder)

        build_system = CMake(self)
        build_system.install()

        if not self.options.shared:
            lib_regex = re.compile(
                r'add_library\((\w+?)\s.*?\)'
                r'(?:(?:#|\w|\s|\()+?'
                r'INTERFACE_LINK_LIBRARIES\s\"((?:;|:|/|\.|\w|\s|-|\(|\))+?)\"'
                r'(?:.|\n)*?\))?'
            )
            exports_file = 'LLVMExports.cmake'
            exports_path = package_path.joinpath('lib', 'cmake', 'llvm')
            exports_path = exports_path.joinpath(exports_file)

            exports = tools.load(str(exports_path.resolve()))
            exports = exports.replace('\$<LINK_ONLY:', '')
            exports = exports.replace('>', '')

            components = {}
            for match in re.finditer(lib_regex, exports):
                lib, deps = match.groups()
                if not lib.startswith('LLVM'):
                    continue

                components[lib] = []
                for dep in deps.split(';') if deps is not None else []:
                    if Path(dep).exists():
                        dep = Path(dep).stem.replace('lib', '')
                    elif dep.startswith('-delayload:'):
                        continue
                    components[lib].append(dep.replace('-l', ''))

            components_path = package_path.joinpath('components.json')
            with components_path.open(mode='w') as file:
                json.dump(components, file, indent=4)

        time.sleep(1)
        tools.rmdir(str(package_path.joinpath('bin').resolve()))
        tools.rmdir(str(package_path.joinpath('lib', 'cmake').resolve()))
        tools.rmdir(str(package_path.joinpath('share').resolve()))

        for lib in package_path.joinpath('lib').iterdir():
            if 'LLVM' not in lib.stem:
                lib.unlink()
        if self.options.shared:
            for lib in package_path.joinpath('lib').glob('*LLVM???*.*'):
                lib.unlink()

    def package_info(self):
        if self.options.shared:
            self.cpp_info.libs = tools.collect_libs(self)
            if self.settings.os == 'Linux':
                self.cpp_info.libs.extend(['tinfo', 'pthread'])
                self.cpp_info.libs.extend(['rt', 'dl', 'm'])
            elif self.settings.os == 'Macos':
                self.cpp_info.libs.extend(['curses', 'm'])
            return

        package_path = Path(self.package_folder)
        components_path = package_path.joinpath('components.json')
        with components_path.open(mode='r') as file:
            components = json.load(file)

        dependencies = ['z', 'iconv', 'xml2', 'ffi']
        targets = {
            'z': 'zlib::zlib',
            'xml2': 'libxml2::libxml2',
            'ffi': 'libffi::libffi'
        }

        for lib, deps in components.items():
            component = lib[4:].replace('LLVM', '').lower()

            self.cpp_info.components[component].libs = [lib]

            self.cpp_info.components[component].requires = [
                dep[4:].replace('LLVM', '').lower()
                for dep in deps if dep.startswith('LLVM')
            ]
            for lib, target in targets.items():
                if lib in deps:
                    self.cpp_info.components[component].requires.append(target)

            self.cpp_info.components[component].system_libs = [
                dep for dep in deps
                if not dep.startswith('LLVM') and dep not in dependencies
            ]
