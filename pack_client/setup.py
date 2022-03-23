from setuptools import setup, find_packages

setup(name='client_chat_pyqt_march_22',
      version='0.1',
      description='Client package',
      author='Evgeniy Varlamov',
      author_email='varlaea2@icloud.com',
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
      )
