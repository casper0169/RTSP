import os
import subprocess
import time
import sys

def run_command(command, wait=True):
    """ Ejecuta un comando en el sistema y muestra el progreso. """
    print(f"Ejecutando: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if stdout:
        print(stdout.decode())
    if stderr:
        print(stderr.decode())
    if process.returncode != 0:
        print(f"Error al ejecutar el comando: {command}")
        sys.exit(1)
    if wait:
        time.sleep(2)  # Espera entre comandos

def show_message(message):
    """ Muestra un mensaje en pantalla """
    print(message)

def open_in_editor(file_path):
    """ Abre un archivo en nano para que el usuario pueda editarlo. """
    print(f"A continuación se abrirá el archivo {file_path} para editarlo.")
    subprocess.Popen(['nano', file_path]).wait()

def set_static_ip():
    """ Configura la dirección IPv4 privada estática """
    show_message("""
Ahora tendrás que modificar el archivo de configuración de la tarjeta de red de tu ordenador / máquina virtual para que tenga una dirección IPv4 privada estática. Copia el siguiente contenido:
version: 2
renderer: NetworkManager
ethernets:
  enp0s3:
    addresses: [192.168.1.200/24]  # IPv4 privada estática para tu ordenador o máquina virtual que albergará al Servidor RTSP
    gateway4: 192.168.1.1  # IPv4 privada de la puerta de enlace de tu Router de Internet
    nameservers:
      addresses:
        - 8.8.8.8  # DNS Primario (Google para evitar fallos)
        - 8.8.4.4  # DNS Secundario (Google para evitar fallos)
    """)

    show_message("PULSA [INTRO] PARA CONTINUAR ó [ESCAPE] PARA CANCELAR EL PROCESO ...")

    # Esperar por la acción del usuario
    option = input()

    if option.lower() == "escape":
        main_menu()

    # Acceder al directorio /etc/netplan/
    run_command("cd /etc/netplan/")

    # Verificar si el archivo 00-installer-config.yaml ya existe
    if not os.path.exists("/etc/netplan/00-installer-config.yaml"):
        # Si el archivo no existe, renombrar el archivo existente
        files = [f for f in os.listdir("/etc/netplan/") if f.endswith(".yaml")]
        if files:
            file_name = files[0]
            run_command(f"sudo mv /etc/netplan/{file_name} /etc/netplan/00-installer-config.yaml")
    
    # Abrir el archivo 00-installer-config.yaml en el editor para que el usuario lo modifique
    open_in_editor("/etc/netplan/00-installer-config.yaml")

    # Esperar a que el usuario cierre el editor
    print("ESPERANDO A QUE SE CIERRE EL ARCHIVO ...")

    # Una vez que se haya cerrado el archivo, cambiar los permisos del archivo 00-installer-config.yaml
    run_command("sudo chmod 644 /etc/netplan/00-installer-config.yaml", wait=False)

    # Aplicar la configuración de netplan y reiniciar NetworkManager
    run_command("sudo netplan apply", wait=False)
    time.sleep(2)
    run_command("sudo systemctl restart NetworkManager", wait=False)
    time.sleep(2)

    print("\033[1m\033[32m********** ¡ENHORABUENA! YA TIENES CONFIGURADA LA TARJETA DE RED DE TU SERVIDOR DE VIDEO EN STREAMING RTSP. **********\033[0m")
    main_menu()

def configure_firewall():
    """ Configura los puertos del firewall """
    show_message("A CONTINUACIÓN VAMOS A CONFIGURAR LOS PUERTIOS DEL FIREWALL PARA EL SERVIDOR DE VIDEO DE STREAMING RTSP")

    # Comprobar si los puertos ya están configurados
    result = subprocess.run(['sudo', 'ufw', 'status'], stdout=subprocess.PIPE)
    if "8554/tcp" in result.stdout.decode():
        show_message("La configuración del firewall ya se ha realizado.")
        choice = input("PARA SOBREESCRIBIR LA CONFIGURTACIÓN PULSE [INTRO], PARA DESCARTAR PULSE [ESCAPE]: ")
        if choice.lower() == "escape":
            main_menu()
        elif choice.lower() == "intro":
            run_command("sudo ufw delete allow 8554/tcp", wait=False)

    # Configuración de puertos
    run_command("sudo apt-get install ufw -y")
    run_command("sudo ufw enable")
    run_command("sudo ufw allow 8554/tcp")
    run_command("sudo ufw status verbose")
    run_command("sudo ufw reload")
    
    print("\033[1m\033[32m********** ¡ENHORABUENA! YA TIENES CONFIGURADOS LOS PÙERTOS DEL FIREWALL DE TU SERVIDOR DE VIDEO EN STREAMING RTSP. **********\033[0m")
    main_menu()

def install_mediamtx():
    """ Instala y configura el servidor de streaming Mediamtx """
    show_message("AHORA PROCEDEREMOS CON LA INSTALACIÓN DEL SERVIDOR DE VIDEO STREAMING RTSP")

    run_command("sudo apt install net-tools -y")
    run_command("sudo apt update && sudo apt full-upgrade -y")
    run_command("sudo apt autoremove -y")
    run_command("curl -L -o mediamtx_v1.10.0_linux_amd64.tar.gz https://github.com/bluenviron/mediamtx/releases/download/v1.10.0/mediamtx_v1.10.0_linux_amd64.tar.gz")
    run_command("chmod 777 *")
    run_command("tar xzf mediamtx_v1.10.0_linux_amd64.tar.gz")
    run_command("chmod 777 *")
    run_command("sudo mv mediamtx.yml /usr/local/etc/")
    run_command("chmod 777 /usr/local/etc/mediamtx.yml")

    show_message("""
A CONTINUACIÓN SE ABRIRÁ UN DOCUMENTO EN EL QUE DEBERÁS DE BUSCAR LO SIGUIENTE:
# The handshake is always performed with TCP.
protocols: [udp, multicast, tcp]

Deberás de borrar 'udp' de manera que resulte:
protocols: [multicast, tcp]
CUANDO LO TENGAS, NO MODIFIQUES NADA MÁS, GUARDA EL DOCUMENTO, CONFIRMA Y CIERRALO.
    """)
    input("Pulsa INTRO para continuar...")

    open_in_editor("/usr/local/etc/mediamtx.yml")

    run_command("sudo mv mediamtx /usr/local/bin/")

    show_message("""
A CONTINUACIÓN SE ABRIRÁ UN DOCUMENTO EN EL QUE DEBERÁS DE PONER LO SIGUIENTE, COPIAR Y PEGAR NO FUNCIONA, PONLO A MANO:
[Unit]
Wants=network.target
[Service]
ExecStart=/usr/local/bin/mediamtx /usr/local/etc/mediamtx.yml
[Install]
WantedBy=multi-user.target

CUANDO LO TENGAS, NO MODIFIQUES NADA MÁS, GUARDA EL DOCUMENTO, CONFIRMA Y CIERRALO.
    """)
    input("Pulsa INTRO para continuar...")

    open_in_editor("/etc/systemd/system/mediamtx.service")

    run_command("chmod 777 /etc/systemd/system/mediamtx.service")
    run_command("sudo systemctl daemon-reload")
    run_command("sudo systemctl restart mediamtx")
    run_command("sudo systemctl enable mediamtx")
    print("\033[1m\033[32m********** ¡ENHORABUENA! YA TIENES CREADO TU SERVIDOR DE VIDEO EN STREAMING RTSP. **********\033[0m")
    main_menu()

def main_menu():
    """ Menú principal """
    while True:
        print("|-----------------------------------------------------------------------------|")
        print("|        MENÚ PRINCIPAL - CONFIGURACIÓN SERVIDOR VIDEO DE STREAMING RTSP      |")
        print("|-----------------------------------------------------------------------------|")
        print("| 1. Configurar la dirección IPv4 Privada Estática                            |")
        print("|-----------------------------------------------------------------------------|")
        print("| 2. Configurar los puertos del Firewall                                      |")
        print("|-----------------------------------------------------------------------------|")
        print("| 3. Instalación del Servidor de Video en Streaming RTSP (mediamtx)           |")
        print("|-----------------------------------------------------------------------------|")
        print("| 0. SALIR                                                                    |")
        print("|-----------------------------------------------------------------------------|")
        choice = input("SELECCIONE UNA OPCIÓN: ")

        if choice == '1':
            set_static_ip()
        elif choice == '2':
            configure_firewall()
        elif choice == '3':
            install_mediamtx()
        elif choice == '0':
            print( "\033[1m\033[32m********** ¡ GRACIAS POR VISITARNOS ! VUELVE PRONTO . **********\033[0m")
            sys.exit(0)  # Salir del script
        else:
            print("\033[1m\033[32m********** ¡OPCIÓN NO VÁLIDA ! INTÉNTALO NUEVAMENTE . **********\033[0m")
           

if __name__ == "__main__":
    main_menu()
