import setuptools

setuptools.setup(
    name='rfcyaml',
    version='0.0.5',
    install_requires=[
        'dacite==1.6.0',
        'PyYAML==5.4.1'
    ],
    author='Ayato Tokubi',
    author_email='tokubi@hongo.wide.ad.jp',
    description='RFC in yaml format',
    url='https://github.com/bitoku/rfcyaml',
    packages=setuptools.find_packages(),
    python_requires='>=3.8',
)