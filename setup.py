from setuptools import setup, find_packages
import os

version = '0.12.1'

setup(name='fieldml.pmr2',
      version=version,
      description="FieldML plugin for PMR2",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='',
      author='Tommy Yu',
      author_email='tommy.yu@auckland.ac.nz',
      url='http://physiome.org.nz/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['fieldml'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          'pmr2.app>=0.14.1',
          'pmr2.rdf',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
