#!/usr/bin/env python

import glob
import os
import shutil
import sys

from distutils.core import setup, Command, Extension
from distutils.command.clean import clean as distutils_clean
from distutils.command.sdist import sdist as distutils_sdist


class clean(distutils_clean):
    def run(self):
        # In addition to what the normal clean run does, remove pyc
        # and pyo and backup files from the source tree.
        distutils_clean.run(self)

        def should_remove(filename):
            if (filename.lower()[-4:] in [".pyc", ".pyo"]
                or filename.endswith("~")
                or (filename.startswith("#")
                    and filename.endswith("#"))):
                return True
            else:
                return False
        for pathname, dirs, files in os.walk(os.path.dirname(__file__)):
            for filename in filter(should_remove, files):
                try:
                    os.unlink(os.path.join(pathname, filename))
                except EnvironmentError as err:
                    print(str(err))

        try:
            os.unlink("MANIFEST")
        except OSError:
            pass

        for base in ["coverage", "build", "dist"]:
            path = os.path.join(os.path.dirname(__file__), base)
            if os.path.isdir(path):
                shutil.rmtree(path)


class coverage_cmd(Command):
    description = "generate test coverage data"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import trace
        tracer = trace.Trace(
            count=True, trace=False,
            ignoredirs=[sys.prefix, sys.exec_prefix])

        def run_tests():
            import bulletml
            try:
                reload(bulletml)
            except NameError:
                pass
            self.run_command("test")

        tracer.runfunc(run_tests)
        results = tracer.results()
        coverage = os.path.join(os.path.dirname(__file__), "coverage")
        results.write_results(show_missing=True, coverdir=coverage)
        map(os.unlink, glob.glob(os.path.join(coverage, "[!b]*.cover")))
        try:
            os.unlink(os.path.join(coverage, "..setup.cover"))
        except OSError:
            pass

        total_lines = 0
        bad_lines = 0
        for filename in glob.glob(os.path.join(coverage, "*.cover")):
            lines = open(filename, "rU").readlines()
            total_lines += len(lines)
            bad_lines += len(
                [line for line in lines if
                 (line.startswith(">>>>>>") and
                  "finally:" not in line and '"""' not in line)])
        pct = 100.0 * (total_lines - bad_lines) / float(total_lines)
        print("Coverage data written to %s (%d/%d, %0.2f%%)" % (
            coverage, total_lines - bad_lines, total_lines, pct))


class sdist(distutils_sdist):
    def run(self):
        self.run_command("test")
        distutils_sdist.run(self)


class test_cmd(Command):
    description = "run automated tests"
    user_options = [
        ("to-run=", None, "list of tests to run (default all)"),
    ]

    def initialize_options(self):
        self.to_run = []
        self.quick = False

    def finalize_options(self):
        if self.to_run:
            self.to_run = self.to_run.split(",")

    def run(self):
        import tests
        if tests.unit(self.to_run):
            raise SystemExit("Test failures are listed above.")

if __name__ == "__main__":
    setup(cmdclass=dict(clean=clean, test=test_cmd, coverage=coverage_cmd,
                        sdist=sdist),
          name="python-bulletml", version="3",
          url="https://yukkurigames.com/python-bulletml/",
          description="parse and run BulletML scripts",
          author="Joe Wreschnig",
          author_email="joe.wreschnig@gmail.com",
          license="MIT-style",
          packages=["bulletml"],
          data_files=glob.glob("examples/*/*.xml") + ["examples/template.xml"],
          scripts=["bulletml-runner", "bulletml-to-bulletyaml"],
          ext_modules=[Extension(
              'bulletml._collision',
              [os.path.join('bulletml', '_collision.c')])],
          long_description="""\
BulletML is the Bullet Markup Language. BulletML can describe the
barrage of bullets in shooting games. (For example Progear, Psyvariar,
Gigawing2, G DARIUS, XEVIOUS, ...) This module parses and executes
BulletML scripts in Python. All data structures in it are
renderer-agnostic. A sample renderer for Pygame is included. The full
API documentation is contained in its Python docstrings.

In addition to the standard BulletML XML format, this module supports
an equivalent YAML format. For convenience, two simple collision
routines are provided, bulletml.overlaps for stationary circles and
bulletml.collides for moving circles.

More information is available at the BulletML homepage,
http://www.asahi-net.or.jp/~cs8k-cyu/bulletml/index_e.html, or the
python-bulletml homepage, https://yukkurigames.com/python-bulletml/.
""")
