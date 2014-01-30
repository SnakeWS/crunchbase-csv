from distutils.core import setup

long_description = open('README.md').read()

setup(name="crunchbase-csv",
      version="0.1",
      description="Convert crunchbase data to CSV",
      author="Eugene Brevdo <ebrevdo@gmail.com>",
      author_email="ebrevdo@gmail.com",
      license="MIT",
      url="http://github.com/ebrevdo/crunchbase-csv",
      long_description=long_description,
      platforms=["any"],
      )
