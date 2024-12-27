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

    show_message("Pulsa INTRO para continuar o ESCAPE para volver al menú inicial ...")

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
    print("Esperando a que se cierre el archivo...")

    # Una vez que se haya cerrado el archivo, cambiar los permisos del archivo 00-installer-config.yaml
    run_command("sudo chmod 644 /etc/netplan/00-installer-config.yaml", wait=False)

    # Aplicar la configuración de netplan y reiniciar NetworkManager
    run_command("sudo netplan apply", wait=False)
    time.sleep(2)
    run_command("sudo systemctl restart NetworkManager", wait=False)
    time.sleep(2)

    show_message("¡Enhorabuena! Ya tienes la tarjeta de red configurada para tu Servidor RTSP.")
    main_menu()

def configure_firewall():
    """ Configura los puertos del firewall """
    show_message("Ahora vamos a configurar los puertos del firewall para el servidor RTSP.")

    # Comprobar si los puertos ya están configurados
    result = subprocess.run(['sudo', 'ufw', 'status'], stdout=subprocess.PIPE)
    if "8554/tcp" in result.stdout.decode():
        show_message("La configuración del firewall ya se ha realizado.")
        choice = input("Para sobrescribir la configuración ya existente pulsa [INTRO], para descartar pulsar [ESCAPE]: ")
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

    show_message("¡Enhorabuena! Ya tienes los puertos del Firewall configurados para tu Servidor RTSP.")
    main_menu()

def install_mediamtx():
    """ Instala y configura el servidor de streaming Mediamtx """
    show_message("Ahora procederemos con la instalación del Servidor de video STREAMING (mediamtx).")

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
A continuación se abrirá un documento en el que deberás buscar lo siguiente:
# The handshake is always performed with TCP.
protocols: [udp, multicast, tcp]

Deberás de borrar 'udp' de manera que resulte:
protocols: [multicast, tcp]
Cuando lo tengas, no modifiques nada más, guarda el documento, confirma y ciérralo.
    """)
    input("Pulsa INTRO para continuar...")

    open_in_editor("/usr/local/etc/mediamtx.yml")

    run_command("sudo mv mediamtx /usr/local/bin/")

    show_message("""
A continuación se abrirá un documento en el que deberás poner lo siguiente, ponlo a mano ya que copiando y pegando no funciona:
[Unit]
Wants=network.target
[Service]
ExecStart=/usr/local/bin/mediamtx /usr/local/etc/mediamtx.yml
[Install]
WantedBy=multi-user.target

Cuando lo tengas, no modifiques nada más, guarda el documento, confirma y ciérralo.
    """)
    input("Pulsa INTRO para continuar...")

    open_in_editor("/etc/systemd/system/mediamtx.service")

    run_command("chmod 777 /etc/systemd/system/mediamtx.service")
    run_command("sudo systemctl daemon-reload")
    run_command("sudo systemctl restart mediamtx")
    run_command("sudo systemctl enable mediamtx")

    show_message("¡Enhorabuena!, ya tienes creado tu Servidor de video en STREAMING (mediamtx).")
    main_menu()

def main_menu():
    """ Menú principal """
    while True:
        print("\nBienvenido al script de configuración para el Servidor RTSP")
        print("[1] Definir la dirección IPv4 privada estática")
        print("[2] Definir los puertos del Firewall")
        print("[3] Instalación del Servidor de Video STREAMING (mediamtx)")
        print("[0] Salir del script")
        choice = input("Seleccione una opción: ")

        if choice == '1':
            set_static_ip()
        elif choice == '2':
            configure_firewall()
        elif choice == '3':
            install_mediamtx()
        elif choice == '0':
            print("Saliendo del script...")
            sys.exit(0)  # Salir del script
        else:
            print("Opción no válida. Intente nuevamente.")

if __name__ == "__main__":
    main_menu()
