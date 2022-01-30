#!/usr/bin/env python3

"""

REQUERIMENTOS   - INSTALAÇÃO
         magic  - pip3 install python-magic --user
"""

__version__ = '0.2.3' 
__author__ = 'Bruno Chaves'
__repo__ = 'https://github.com/Brunopvh/cmd-lib'
__download_file__ = 'https://github.com/Brunopvh/cmd-lib/archive/refs/heads/main.zip'

import sys
import os
import hashlib

from shutil import (
    which,
    copytree,
    copy,
    rmtree,
    unpack_archive,
)

from subprocess import (
    PIPE,
    Popen,
    run as subprocess_run
)

from pathlib import Path

try:
    from magic import from_file
except Exception as e:
    print(e)
    sys.exit(1)


def get_term_col() -> int:
    """Retorna o número de colunas do terminal"""
    try:
        _col: int = os.get_terminal_size()[0]
    except:
        _col: int = 60

    return _col


class ExecShellCommand(object):
    """
       Classe para executar comandos shell, apartir da lista 'self.cli'
    """
    
    def __init__(self, cli: list=[]) -> None:
        super().__init__()
        self.cli: list = cli
        self.isproc: bool = False
        self.returnbool: bool = True
        self.returncode: int = 0
        self.text_exit = None
        self.current_line = None

    @property
    def cli(self) -> list:
        return self._cli

    @cli.setter
    def cli(self, new_cli) -> None:
        if not isinstance(new_cli, list):
            print(f'{__class__.__name__} ERRO os comandos devem ser passados como lista.')
            return
        self._cli = new_cli

    @property
    def isproc(self) -> bool:
        return self._isproc

    @isproc.setter
    def isproc(self, isproc) -> None:
        self._isproc = isproc

    def get_process(self) -> Popen:
        """
           Retorna um objeto do tipo Popen(), com os comandos de self.cli
        se outro processo criando anteriormente por esta classe ainda estiver
        em execução, o retorno será None. 
        """
        if self.cli == []:
            return None

        if self.isproc:
            print(f'{__class__.__name__} outro processo já está em execução, aguarde...')
            return None

        try:
            _proc: Popen = Popen(self.cli, stdin=PIPE, stdout=PIPE, stderr=PIPE, encoding='utf8')
        except Exception as e:
            print(e)
            return None

        self.isproc = True
        return _proc

    def exec(self) -> None:
        """
          Executa um comando e exibe as linhas de saída no stdout.
        """
        proc: Popen = self.get_process()
        if proc is None:
            self.returnbool = False
            self.returncode = 1
            self.text_exit = None
            return

        for line in proc.stdout:
            self.current_line = line
            print(line, end=' ')
            sys.stdout.flush()
        print()
        proc.wait()

        self.returncode = proc.returncode
        self.isproc = False
        if proc.returncode == 0:
            self.returnbool = True
            self.text_exit = proc.communicate()[0]
        else:
            self.returnbool = False
            self.text_exit = proc.stderr
            print(f'EXIT -> {self.returncode}')

        self.cli.clear()

    def exec_silent(self) -> bool:
        """
          Executa um comando sem exibir nada no stdout, apenas ERROS serão exibidos
        no stderr após a execução do comando.
        """
        self.isproc = True
        try:
            proc = subprocess_run(self.cli, text=True, capture_output=True)
        except Exception as e:
            print(e)
            self.returnbool = False
            self.returncode = 1
            self.text_exit = None
            self.isproc = False
            
        self.returncode = proc.returncode
        self.isproc = False
        if proc.returncode == 0:
            self.returnbool = True
            self.text_exit = proc.stdout
        else:
            self.returnbool = False
            self.text_exit = proc.stderr
        self.cli.clear()



if sys.platform == 'linux':
   
    def is_admin() -> bool:
        """
          Verificar se o usuário atual é administrador
        Requerimentos: 
           comando 'id' no linux. (id --user)
        """
        if os.geteuid() == 0:
            return True
       
        print("Verificando se você é administrador ...", end=' ')
        sys.stdout.flush()
        proc = ExecShellCommand(['sudo', 'sh', '-c', 'id --user'])
        proc.exec_silent()
        return proc.returnbool

    def sudo_command(cmds: list) -> bool:
        """
           Executa comandos com o sudo.  
        Ex:
          mkdir /teste

        sudo_command(['mkdir', '/teste'])    
        """
        if not isinstance(cmds, list):
            raise Exception('sudo_command ERRO ... os comandos precisam ser passados em forma de lista.')

        cmds.insert(0, 'sudo')
        print('-' * get_term_col())
        print('Executando ...', end=' ')
        
        for c in cmds:
            print(c, end=' ')
        print()
        print('-' * get_term_col())

        proc = ExecShellCommand(cmds)
        proc.exec()
        return proc.returnbool


    def device_ismounted(device: str) -> bool:
        """
          Verifica se um dispositivo está montado.
        diferente de os.path.ismount(path) que verifica se um caminho é ponto de montagem, este
        metódo trabalha com um dispositivo (/dev/sda1, /dev/sda2, ...)
        """

        if os.name != 'posix':
            return False

        if '/dev/loop' in device:
            try:
                with open('/proc/mounts', 'rt') as f:
                    mounts = f.read()
            except Exception as e:
                print('ERRO', e)
                return False
        else:
            proc = ExecShellCommand(['mount'])
            proc.exec_silent()
            mounts = proc.text_exit

        _ismount: bool = False
        for num, line in enumerate(mounts.split('\n')):
            if num < len(mounts.split('\n')) - 1:
                if (line.split()[0] == device) and (len(line.split()[0]) == len(device)):
                    _ismount = True
                    break

        return _ismount



class ByteSize(int):
    """
      Classe para mostrar o tamaho de um arquivo (B, KB, MB, GB) de modo legível para humanos.
    """

    # https://qastack.com.br/programming/1392413/calculating-a-directorys-size-using-python
    # 2021-11-13 - 21:12
    
    _kB = 1024
    _suffixes = 'B', 'kB', 'MB', 'GB', 'PB'

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        self.bytes = self.B = int(self)
        self.kilobytes = self.kB = self / self._kB**1
        self.megabytes = self.MB = self / self._kB**2
        self.gigabytes = self.GB = self / self._kB**3
        self.petabytes = self.PB = self / self._kB**4
        *suffixes, last = self._suffixes
        suffix = next((
            suffix
            for suffix in suffixes
            if 1 < getattr(self, suffix) < self._kB
        ), last)
        self.readable = suffix, getattr(self, suffix)

        super().__init__()

    def __str__(self):
        return self.__format__('.2f')

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, super().__repr__())

    def __format__(self, format_spec):
        suffix, val = self.readable
        return '{val:{fmt}} {suf}'.format(val=val, fmt=format_spec, suf=suffix)

    def __sub__(self, other):
        return self.__class__(super().__sub__(other))

    def __add__(self, other):
        return self.__class__(super().__add__(other))

    def __mul__(self, other):
        return self.__class__(super().__mul__(other))

    def __rsub__(self, other):
        return self.__class__(super().__sub__(other))

    def __radd__(self, other):
        return self.__class__(super().__add__(other))

    def __rmul__(self, other):
        return self.__class__(super().__rmul__(other))



class FileSize(object):
    """Obeter o tamanho de arquivos e diretórios com python."""
    def __init__(self, path: str):
        self.path: str = path # arquivo/diretório.

    def _get_folder_size(self) -> float:
        _path: Path = Path(self.path)
        total: float = 0.0
        for item in _path.rglob('*'):
            total += os.path.getsize(item)
        return total

    def _get_file_size(self) -> float:
        return float(os.path.getsize(self.path))

    def get_size(self) -> float:
        if os.path.isdir(self.path):
            return self._get_folder_size()
        else:
            return self._get_file_size()

    def number_size(self) -> float:
        """
        ESTE MÉTODO FOI DESCONTINUADO. Use self.get_size()
          Retorna o tamanho em bytes de um arquivo/diretório.
        """
        return self.get_size()

    def human_size(self) -> ByteSize:
        """Retorna o tamaho de um arquivo ou diretório de maneira legivel a humanos."""
        return ByteSize(int(self.get_size()))



class ShellCoreUtils(object):
    """Classe para executar operações básicas de sistemas, como:
    
    - copiar arquivos
    - mover arquivos
    - apagar arquivos
    - criar diretórios
    - criar arquivos.
    - obter o tamanho de arquivos
    - obter a extensão de um arquivo
    - obter o tipo de arquivo via cabeçãlho
    """
    def __init__(self) -> None:
        super().__init__()

    def copy(self, SRC: str, DEST: str) -> bool:
        pass

    def rmdir(self, path: str) -> bool:
        pass

    def mkdir(self, path: str) -> bool:
        pass

    def file_size(self, file: str, human=False) -> float:
        pass

    def get_header_file(self, file) -> str:
        """Retorna o cabeçalho de um arquivo."""
        pass

    def get_extension_file(self, file) -> str:
        """Retorna a extensão de um arquivo."""
        pass

    def get_type_file(self, file: str) -> str:
        """Retorna o tipo de arquivo, com base no cabeçalho"""
        pass

    def device_ismounted(self, device: str) -> bool:
        pass



class LinuxShellCore(ShellCoreUtils):
   
    def __init__(self, *, exec_root: bool = False, verbose=False):
        
        super().__init__()
        # Os comandos podem ser executados como root por meio do sudo (apenas em sistemas posix).
        # se exec_root for True, o comando sudo será inserido no comando a ser executado.
        if sys.platform == 'linux':
            if which('sudo') is None:
                print(f'{__class__.__name__} comando [sudo] não está disponível.')

        self.exec_root: bool = exec_root
        self.verbose: bool = verbose
        self._cmd_list = []
        self._exec_commands: ExecShellCommand = ExecShellCommand(self._cmd_list)

    @property
    def exec_root(self) -> bool:
        return self._exec_root

    @exec_root.setter
    def exec_root(self, new_exec_root: bool) -> None:
        self._exec_root = new_exec_root

    def print_msg(self, text: str) -> None:
        if not self.verbose:
            return
        print(text)
        sys.stdout.flush()

    def copy(self, SRC: str, DEST: str) -> bool:
        """Copia arquivos é diretórios com o cp do Linux."""
       
        self.print_msg(f'Copiando ... {SRC}')
        self._exec_commands.cli = ['cp', '-R', SRC, DEST]
        
        if self.exec_root:
            self._exec_commands.cli.insert(0, 'sudo')

        self._exec_commands.exec()
        return self._exec_commands.returnbool

    def mkdir(self, path: str) -> bool:
        """Cria diretórios com o mkdir"""
        self.print_msg(f'Criando ditetório ... {path}')
        if os.system(f'mkdir -p {path}') == 0:
            return True
        return False

    def rmdir(self, path: str) -> bool:
        """Apaga arquivos e diretórios usando o rm do Linux."""
        self.print_msg(f'Deletando ... {path}')
        if os.system(f'rm -rf {path}') == 0:
            return True
        return False

    def file_size(self, path, *, human=False) -> str:
        """Retorna o tamanho de arquivos e diretórios"""
        self._cmd_list.clear()

        # Adicionar o "/" no final do diretório se não existir
        # DIR = /path/foo => DIR = /path/foo/
        if os.path.isdir(path):
            if path[-1:] != '/':
                path += '/'

        if human:
            self._exec_commands.cli = ['du', '-hs', path]
        else:
            self._exec_commands.cli = ['du', '-s', path]

        if self.exec_root:
            self._exec_commands.cli.insert(0, 'sudo')

        self._exec_commands.cli = self._cmd_list
        self._exec_commands.exec_silent()
        if not self._exec_commands.returnbool: 
            return -1.0

        return str((self._exec_commands.text_exit).split()[0])

    def get_header_file(self, file) -> str:
        """Retorna o cabeçalho de um arquivo."""
        self._exec_commands.cli = ['file', file]
        self._exec_commands.exec_silent()
        return str(self._exec_commands.text_exit)

    def get_type_file(self, file: str) -> str:
        """Retorna o tipo de arquivo, com base no cabeçalho"""
        return self.get_header_file(file).split()[1] 

    def device_ismounted(self, device: str) -> bool:
        """
          Verifica se um dispositivo está montado.
        diferente de os.path.ismount(path) que verifica se um caminho é ponto de montagem, este
        metódo trabalha com um dispositivo (/dev/sda1, /dev/sda2, ...)
        """

        if '/dev/loop' in device:
            try:
                with open('/proc/mounts', 'rt') as f:
                    mounts = f.read()
            except Exception as e:
                print(f'{__class__.__name__} {e}')
                return False
        else:
            proc = ExecShellCommand(['mount'])
            proc.exec_silent()
            mounts = proc.text_exit

        _ismount: bool = False
        for num, line in enumerate(mounts.split('\n')):
            if num < len(mounts.split('\n')) - 1:
                if (line.split()[0] == device) and (len(line.split()[0]) == len(device)):
                    _ismount = True
                    break

        return _ismount



class PythonShellCore(ShellCoreUtils):
    """
       Executar operações como copiar, remover, descompactar entre outras usando módulos
    nativos do Python, sem as ferramentas Unix/Linux.
    """

    def __init__(self, *, exec_root: bool=False, verbose=False) -> None:
        super().__init__()
        self._cmd_list = []
        self.returnbool: bool = True
        self.exception_text = None
        self.exception_type = None
        self.verbose = verbose

    def print_msg(self, text: str) -> None:
        if not self.verbose:
            return
        print(text, end=' ')
        sys.stdout.flush()

    def _copy_dir(self, src: str, dest: str) -> bool:
        """Método interno para copiar diretórios"""
        try:
            copytree(src, dest, symlinks=True, ignore=None)
        except Exception as e:
            print(__class__.__name__, e)
            self.exception_text = e
            self.exception_type = type(e)
            self.returnbool = False
            return False
        else:
            self.exception_text = None
            self.exception_type = None
            self.returnbool = True
            return True

    def _copy_files(self, src: str, dest: str) -> bool:
        """Método interno para copiar arquivos"""
        try:
            copy(src, dest, follow_symlinks=False)
        except Exception as e:
            print(__class__.__name__, e)
            self.exception_text = e
            self.exception_type = type(e)
            self.returnbool = False
            return False
        else:
            self.exception_text = None
            self.exception_type = None
            self.returnbool = True
            return True

    def copy(self, src: str, dest: str) -> bool:
        """Copia arquivos e diretórios."""
        if os.path.isdir(src):
            return self._copy_dir(src, dest)
        else:
            return self._copy_files(src, dest)

    def mkdir(self, path: str) -> bool:
        """Cria um diretório."""
        try:
            os.makedirs(path)
        except(PermissionError):
            print(f'{__class__.__name__} você não tem permissão de escrita em ... {path}')
            self.exception_type = 'PermissionError'
            self.returnbool = False
            return False
        except(FileExistsError):
            self.exception_type = 'FileExistsError'
            if os.access(path, os.W_OK):
                self.returnbool = True
                return True
            self.returnbool = False
            return False
        except Exception as e:
            print(__class__.__name__, e)
            self.returnbool = False
            self.exception_text = e
            self.exception_type = type(e)
            return False

    def _rmfile(self, path) -> bool:
        """Método interno para remover um arquivo."""
        try:
            os.remove(path)
        except Exception as e:
            print(__class__.__name__, e)
            self.exception_text = e
            self.exception_type = type(e)
            self.returnbool = False
            return False
        else:
            self.exception_text = None
            self.exception_type = None
            self.returnbool = True
            return True

    def _rmdirectory(self, path) -> bool:
        """Método interno para remover um diretório."""
        try:
            rmtree(path)
        except Exception as e:
            print(__class__.__name__, e)
            self.exception_text = e
            self.exception_type = type(e)
            self.returnbool = False
            return False
        else:
            self.exception_text = None
            self.exception_type = None
            self.returnbool = True
            return True

    def _rmlink(self, path) -> bool:
        try:
            os.unlink(path)
        except Exception as e:
            print(__class__.__name__, e)
            self.exception_text = e
            self.exception_type = type(e)
            self.returnbool = False
            return False
        else:
            self.exception_text = None
            self.exception_type = None
            self.returnbool = True
            return True

    def rmdir(self, path: str) -> bool:
        '''
        Remove Arquivos e diretórios.
        '''
        self.print_msg(f'Deletando ... {path}')

        if os.path.isdir(path):
            return bool(self._rmdirectory(path))
        elif os.path.islink(path):
            return bool(self._rmlink(path))
        elif os.path.isfile(path):
            return bool(self._rmfile(path))
        elif not os.path.exists(path):
            self.exception_type = 'FileNotFoundError'
            self.exception_text = f'Arquivo ou diretório não encontrado ... {path}'
            self.returnbool = False
            print(self.exception_text)
            return False
        return False

    def file_size(self, path, *, human=False) -> float:
        """
          Retorna o tamanho de um arquivo ou diretório.
        """
        if not human:
            return FileSize(path).get_size()
        return  FileSize(path).human_size()

    def get_header_file(self, file: str) -> str:
        """Retorna o cabeçalho de um arquivo."""
        return str(from_file(file))

    def get_extension_file(self, file) -> str:
        """Retorna o tipo de arquivo baseado no cabeçalho"""
        return self.get_header_file(file).split()[0]

    def get_type_file(self, file: str) -> str:
        """Retorna o tipo de arquivo baseado no cabeçalho"""
        return self.get_header_file(file).split()[0]


#===============================================================#

shellcore = PythonShellCore()

#===============================================================#

class File(object):
    """
    Classe para gerenciar um arquivo.
    """
    def __init__(self, file: str) -> None:
        super().__init__()
        self.file = file

    def ext(self) -> str:
        """Retorna a extensão do arquivo baseada no nome."""
        file_ext = os.path.splitext(self.file)
        if file_ext[1] == '':
            return None
        return file_ext[1]

    def name(self) -> str:
        return os.path.basename(self.file)

    def dirname(self) -> str:
        """Retorna o diretório Pai do arquivo"""
        if not self.exists():
            return None
        return os.path.dirname(self.path())

    def path(self) -> str:
        """
           Retorna o caminho absoluto do arquivo
        """
        try:
            if not self.exists():
                return None
        except:
            return None
        else:
            return os.path.abspath(self.file)

    def header(self):
        """Retorna o cabeçalho do arquivo."""
        if not self.exists():
            return None
        return PythonShellCore().get_header_file(self.path())

    def extension_file(self):
        """Retorna o tipo de arquivo baseado no cabeçalho"""
        if not self.exists():
            return None
        #return PythonShellCore().get_extension_file(self.path())
        return shellcore.get_type_file(self.path())

    def size(self) -> int:
        """Retorna o tamanho do arquivo em bytes, se o arquivo existir"""
        if not self.exists():
            return 0
        return os.path.getsize(self.path())

    def exists(self) -> bool:
        """Verifica se o arquivo existe."""
        if self.file is None:
            return False
        return os.path.isfile(self.file)



class UnpackLinux(object):
    """Classe para descompactar arquivos usando ferramentas Linux."""

    def __init__(self, *, output_dir=os.getcwd()):
        self.output_dir = output_dir
        self.returnbool = True # OK/ERRO (True/False)

    def unpack(self, path_file: File) -> bool:
        """
            Descompacta arquivos usando as ferramentas de linha de comando Linux.
        """
        # Setar a linha de comando para descomprimir o arquivo, de acordo com
        # a extensão/tipo de arquivo.
        if path_file.extension_file() == 'XZ':
            command_unpack = ["tar", "-Jxf", path_file.path(), "-C", self.output_dir]
        elif path_file.extension_file() == 'bzip2':
            command_unpack = ["tar", "-jxvf", path_file.path(), "-C", self.output_dir]
        elif path_file.extension_file() == 'gzip':
            command_unpack = ["tar", "-zxvf", path_file.path(), "-C", self.output_dir]
        elif path_file.extension_file() == 'Zip':
            command_unpack = ["unzip", "-u", path_file.path(), "-d", self.output_dir]
        elif path_file.extension_file() == 'Debian':
            if os.path.isfile('/etc/debian_version'):
                command_unpack = ["dpkg-deb", "-x", path_file.path(), self.output_dir]
            else:
                command_unpack = ["ar", "-x", path_file.path(), "--output", self.output_dir]
        else:
            print(f'{__name__} ERRO arquivo não suportado {path_file.name()}')
            sys.stdout.flush()
            return False

        exec_proc = ExecShellCommand(command_unpack)
        exec_proc.exec_silent()
        self.returnbool = exec_proc.returnbool
        return self.returnbool


class ShutilUnpack(object):
    """Descompactar arquivos usando shutil."""
    def __init__(self, *, output_dir=os.getcwd(), format: str):
        self.output_dir = output_dir
        self.returnbool = True # OK/ERRO (True/False)
        self.format = format

    def unpack(self, path_file: File) -> bool:
        """
            Recebe um objeto/File para ser descompactado em self.output_dir.
        path_file = Instância da classe File().
        """
   
        try:
            unpack_archive(path_file.path(), extract_dir=self.output_dir, format=self.format)
        except Exception as e:
            print(e)
            self.returnbool = False
        else:
            self.returnbool = True
        
        return self.returnbool



def unpack(compressed_file: str, *, output_dir: str=os.getcwd(), verbose :bool=True) -> bool:
    """
        Descompacta arquivos.
    compresse_file = caminho absoluto do arquivo a ser descomprimido.
    output_dir     = destino dos dados a serem descomprimidos.
    verbose        = bool
    """

    # Setar o formato de arquivo.
    # FORMATO - TIPO
    #    tar    XZ
    #    tar    bzip2
    #    tar    gzip
    #    zip    Zip

    path_file: File = File(compressed_file)
   
    if path_file.extension_file() == 'XZ':
        FORMAT = "tar"
    elif path_file.extension_file() == 'bzip2':
        FORMAT = "tar"
    elif path_file.extension_file() == 'gzip':
        FORMAT = "tar"
    elif path_file.extension_file() == 'Zip':
        FORMAT = "zip"
    
    """
    if (path_file.extension_file() == 'Debian') and (sys.platform == 'linux'):
        unpack_file: UnpackLinux = UnpackLinux(output_dir=output_dir)
    else:
        unpack_file: ShutilUnpack = ShutilUnpack(output_dir=output_dir, format=FORMAT)
    """

    if sys.platform == 'linux':
        unpack_file: UnpackLinux = UnpackLinux(output_dir=output_dir)
    else:
        unpack_file: ShutilUnpack = ShutilUnpack(output_dir=output_dir, format=FORMAT)
    

    if verbose:
        print(f'Descompactando ... {path_file.name()}', end=' ')
        sys.stdout.flush()
        
    unpack_file.unpack(path_file)
    if verbose and unpack_file.returnbool:
        print('OK')
    return unpack_file.returnbool
        
    
#===============================================================#
# Hash utils
#===============================================================#

def get_bytes(data) -> bytes:
    """
        data = arquivo/string/bytes
    converte data para bytes e retorna bytes.
    """
    if isinstance(data, bytes):
        return data

    if isinstance(data, str):
        # Verificar se data é um texto ou um arquivo.
        _bytes = None
        if os.path.isfile(data):
            try:
                with open(data, 'rb') as file:
                    _bytes = file.read()
            except Exception as e:
                print(e)
        else:
            _bytes = str.encode(data)
        return _bytes    



class ShaSumUtils(object):
    def __init__(self) -> None:
        super().__init__()
    
    def _get_bytes(self, data) -> bytes:
        """
            data = arquivo/string/bytes
        converte data para bytes e retorna bytes.
        """
        if isinstance(data, bytes):
            return data

        if isinstance(data, str):
            # Verificar se data é um texto ou um arquivo.
            _bytes = None
            if os.path.isfile(data):
                try:
                    with open(data, 'rb') as file:
                        _bytes = file.read()
                except Exception as e:
                    print(e)
            else:
                _bytes = str.encode(data)
            return _bytes

    def getmd5(self, data) -> str:
        """
        Retorna a hash md5 de data.
        data = arquivo/texto/bytes
        """
        pass

    def getsha1(self, data) -> str:
        """
        Retorna a hash sha1 de data.
        data = arquivo/texto/bytes
        """
        pass
        
    def getsha256(self, data) -> str:
        """
        Retorna a hash sha256sum de data.
        data = arquivo/texto/bytes
        """
        pass

    def getsha512(self, data) -> str:
        """
        Retorna a hash sha512 de data.
        data = arquivo/texto/bytes
        """
        pass

    def check_md5(self, data, md5_string: str) -> bool:
        pass

    def check_sha1(self, data, sha1_string: str) -> bool:
        pass

    def check_sha256(self, data, sha256_string: str) -> bool:
        pass

    def check_sha512(self, data, sha512_string: str) -> bool:
        pass

    def check_md5(self, data, md5_string: str) -> bool:
        if len(md5_string) != 32:
            print(f'{__class__.__name__} ERRO hash do tipo md5 deve ter 32 caracteres.')
            return False

        if self.getmd5(data) == md5_string:
            return True

        print(f'{__class__.__name__} FALHA')
        return False

    def check_sha1(self, data, sha1_string: str) -> bool:
        if len(sha1_string) != 40:
            print(f'{__class__.__name__} ERRO hash do tipo sha1 deve ter 40 caracteres.')
            return False

        if self.getsha1(data) == sha1_string:
            return True

        print(f'{__class__.__name__} FALHA')
        return False

    def check_sha256(self, data, sha256_string: str) -> bool:
        if len(sha256_string) != 64:
            print(f'{__class__.__name__} ERRO hash do tipo sha256 deve ter 64 caracteres.')
            return False

        if self.getsha256(data) == sha256_string:
            return True

        print(f'{__class__.__name__} FALHA')
        return False

    def check_sha512(self, data, sha512_string: str) -> bool:
        if len(sha512_string) != 128:
            print(f'{__class__.__name__} ERRO hash do tipo sha512 deve ter 128 caracteres.')
            return False

        if self.getsha512(data) == sha512_string:
            return True

        print(f'{__class__.__name__} FALHA')
        return False


class ShaSum(ShaSumUtils):
    def __init__(self) -> None:
        super().__init__()

    def getmd5(self, data) -> str:
        """
        Retorna a hash md5 de data.
        data = arquivo/texto/bytes
        """
        data_bytes = get_bytes(data)
        if data_bytes is None:
            return None
        return hashlib.md5(data_bytes).hexdigest()

    def getsha1(self, data) -> str:
        """
        Retorna a hash sha1 de data.
        data = arquivo/texto/bytes
        """
        data_bytes = get_bytes(data)
        if data_bytes is None:
            return None
        return hashlib.sha1(data_bytes).hexdigest()
        
    def getsha256(self, data) -> str:
        """
        Retorna a hash sha256sum de data.
        data = arquivo/texto/bytes
        """
        data_bytes = get_bytes(data)
        if data_bytes is None:
            return None
        return hashlib.sha256(data_bytes).hexdigest()

    def getsha512(self, data) -> str:
        """
        Retorna a hash sha512 de data.
        data = arquivo/texto/bytes
        """
        data_bytes = get_bytes(data)
        if data_bytes is None:
            return None
        return hashlib.sha512(data_bytes).hexdigest()


class ShaSumLinux(ShaSumUtils):
    def __init__(self) -> None:
        super().__init__()

    def __get_output(self, cmds: list):
        proc = ExecShellCommand(cmds)
        proc.exec_silent()
        return proc.text_exit
        
    def getmd5(self, data: str) -> str:
        """Recebe um arquivo e retorna sua hash md5"""
        return self.__get_output(['md5sum', data]).split()[0]
        
    def getsha1(self, data) -> str:
        return self.__get_output(['sha1sum', data]).split()[0]

    def getsha256(self, data) -> str:
        return self.__get_output(['sha256sum', data]).split()[0]

    def getsha512(self, data) -> str:
        return self.__get_output(['sha512sum', data]).split()[0]

#===============================================================#

shasum: ShaSum = ShaSum()

#===============================================================#

class GpgUtils(object):
    def __init__(self) -> None:
        super().__init__()
        
    def importKeyFile(self, file) -> bool:
        pass

    def importKeyData(self, file) -> bool:
        pass

    def verifyFile(self, *, file: str, sign_file: str) -> bool:
        pass

    
class GpgLinux(GpgUtils):
    def __init__(self) -> None:
        super().__init__()

    def importKeyFile(self, file) -> bool:
        proc = ExecShellCommand(['gpg', '--import', file])
        proc.exec_silent()
        return proc.returnbool

    def verifyFile(self, *, file: str, sig_file: str) -> bool:
        #if os.system(f'gpg --verify {sig_file} {file}') == 0:
        #   return True
        #return False
        proc = ExecShellCommand(['gpg', '--verify', sig_file, file])
        proc.exec_silent()
        return proc.returnbool
   
    
gpg_utils = GpgLinux()

def main():
    pass

    
if __name__ == '__main__':
    main()
