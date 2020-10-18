from conans import ConanFile, CMake, tools

from pathlib import Path


class LLVMTestPackageConan(ConanFile):
    settings = ('os', 'arch', 'compiler', 'build_type')
    generators = ('cmake', 'cmake_find_package')

    def build(self):
        build_system = CMake(self)
        build_system.configure()
        build_system.build()

    def test(self):
        test_package = not tools.cross_building(self.settings)
        if 'x86' not in str(self.settings.arch).lower():
            test_package = False
        elif str(self.options['llvm'].targets) not in ['all', 'X86']:
            test_package = False
        elif self.options['llvm'].shared:
             if self.options['llvm'].components != 'all':
                 if not all([
                     target in str(self.options['llvm'].components)
                     for target in ['interpreter', 'irreader', 'x86codegen']
                 ]):
                     test_package = False

        if test_package:
            executable = Path('bin').joinpath('test_package')
            input = Path(__file__).parent.joinpath('test_function.ll')
            command = [str(file.resolve()) for file in (executable, input)]
            self.run(command, run_environment=True)

        llvm_path = Path(self.deps_cpp_info['llvm'].rootpath)
        license_file = llvm_path.joinpath('licenses', 'LICENSE.txt')
        assert license_file.exists()
