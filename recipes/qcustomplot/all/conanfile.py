from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualRunEnv
from conan.tools.files import apply_conandata_patches, copy, get, export_conandata_patches, replace_in_file
from conan.tools.scm import Version
import os

required_conan_version = ">=1.56.0 <2 || >=2.0.6"

class QCustomPlotConan(ConanFile):
    name = "qcustomplot"
    package_type = "library"
    description = "QCustomPlot is a Qt C++ widget for plotting and data visualization."
    license = "GPL-3.0-only"
    topics = ("chart", "data-visualization", "graph", "plot", "qt")
    homepage = "https://www.qcustomplot.com"
    url = "https://github.com/conan-io/conan-center-index"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_opengl": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_opengl": False,
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def requirements(self):
        self.requires("qt/6.4.2", transitive_headers=True, transitive_libs=True)

        if self.options.with_opengl and self.settings.os == "Windows":
            self.requires("opengl/system")

    def build_requirements(self):
        self.tool_requires("qt/<host_version>")

    def validate(self):
        if self.settings.os == "Macos":
            raise ConanInvalidConfiguration(f"{self.ref} Macos not supported at this moment")
        if self.info.settings.compiler.cppstd:
            min_cppstd = "11" if Version(self.dependencies["qt"].ref.version) < "6.0.0" else "17"
            check_min_cppstd(self, min_cppstd)
        if not (self.dependencies["qt"].options.gui and self.dependencies["qt"].options.widgets):
            raise ConanInvalidConfiguration(f"{self.ref} requires qt gui and widgets")
        if self.info.options.with_opengl and self.dependencies["qt"].options.opengl == "no":
            raise ConanInvalidConfiguration(f"{self.ref} with opengl requires Qt with opengl enabled")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version],
            destination=self.source_folder, strip_root=True)

    def generate(self):
        VirtualRunEnv(self).generate(scope="build")

        tc = CMakeToolchain(self)
        tc.variables["QCUSTOMPLOT_SRC_DIR"] = self.source_folder.replace("\\", "/")
        tc.variables["QCUSTOMPLOT_VERSION"] = self.version
        tc.variables["QCUSTOMPLOT_VERSION_MAJOR"] = str(Version(self.version).major)
        tc.variables["QT_VERSION"] = self.dependencies["qt"].ref.version
        tc.variables["QCUSTOMPLOT_USE_OPENGL"] = self.options.with_opengl
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)
        # allow static qcustomplot with shared qt, and vice versa
        replace_in_file(self, os.path.join(self.source_folder, "qcustomplot.h"),
                                "#if defined(QT_STATIC_BUILD)",
                                "#if 0" if self.options.shared else "#if 1")

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure(build_script_folder=os.path.join(self.source_folder, os.pardir))
        cmake.build()

    def package(self):
        copy(self, "GPL.txt", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        postfix = "d" if self.settings.build_type == "Debug" else ""
        self.cpp_info.libs = [f"qcustomplot{postfix}"]
        self.cpp_info.requires = ["qt::qtCore", "qt::qtGui", "qt::qtWidgets", "qt::qtPrintSupport"]
        if self.options.shared:
            self.cpp_info.defines.append("QCUSTOMPLOT_USE_LIBRARY")
        if self.options.with_opengl:
            self.cpp_info.defines.append("QCUSTOMPLOT_USE_OPENGL")
            self.cpp_info.requires.append("qt::qtOpenGL")
            if self.settings.os == "Windows":
                self.cpp_info.requires.append("opengl::opengl")
