import os

from conans import ConanFile, CMake, tools


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def build(self):
        cmake = CMake(self)
        cmake.definitions["TEST_SHARED_LIBRARY"] = self.options["physx"].shared or "fPIC" not in self.options["physx"].fields or ("fPIC" in self.options["physx"].fields and self.options["physx"].fPIC)
        cmake.configure()
        cmake.build()

    def test(self):
        if not tools.cross_building(self.settings):
            bin_path = os.path.join("bin", "test_package")
            self.run(bin_path, run_environment=True)
