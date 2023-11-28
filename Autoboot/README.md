# Autoboot for ZXTRES Cores

Copyright (c) 2023, kounch

All rights reserved.

---

Select your desired language / Elija idioma:

- Click [this link for English](#english)

- Pulse [este enlace para Castellano](#castellano)

---

## English

### Required Hardware

- ZXTRES, ZXTRES+ or ZXTRES++ (middle board is needed for to load BIT files)
- microSD card

*NOTE:* It is recommended to have the Spectrum EXP28 090923 core installed as
the main corem as well as, for the use of the middle board, bootstrap v1.03 or
later, USB v01.02 or later, USB v01.02 or later and MIDI v01.08 or later.

### Required software

- [esxdos](http://esxdos.org) compatible with the version installed in SPI flash
  (the most recent at the moment is 0.8.9)
- zxunocfg "dot" command (available at [ZXTRES official repository](https://github.com/zxtres/dot_commands/tree/main/zxunocfg)
- [Bob Fossil's NMI browser](http://www.thefossilrecord.co.uk/wp-content/uploads/zx/BROWSE_latest.zip)
- BIT and/or ZX3 plugin installed in BIN/BPLUGINS/BIT

### Installation

1. Edit /SYS/CONFIG/ESXDOS.CFG and set AutoBoot=1
2. Depending on where you want the core files to be placed (/CORES, /CORES/BIT
   or /CORES/ZX3), copy to the card the corresponding autoboot program, renamed
   as /SYS/AUTOBOOT.BAS
3. Enter the advanced BIOS settings and set the speed to 8X, and in Main set the
   startup pause to 0 (Disabled)
4. Copy the BIT and/or ZX3 files to be used into the chosen directory at step 2

### How to create a microSD from scratch

1. Format using FAT32

   For cards of the appropriate size (32GB or less for FAT32), you can use the
   official [SD Association formatting tool](https://www.sdcard.org/downloads/formatter/)

   If you are on macOS, it may also be useful to use these commands afterwards so
   that the system does not index the card, deleted files aren't sent to the bin.

         mdutil -i off /Volumes/<microSD name>
         cd /Volumes/<microSD name>
         dot_clean . -n && find . -name ".DS*" -exec rm {} ;
         cd -

2. Download esxdos: <http://esxdos.org> and copy to the card the directories
   BIN, SYS and TMP

3. Download the ZXTRES utilities from
   <https://github.com/zxdos/zxuno/tree/master/SD/BIN> and
   <https://github.com/zxtres/dot_commands/> and copy at least the following files
   (although it is recommended to use all):

         BIN/BPLUGINS/BIT
         BIN/BPLUGINS/MID
         BIN/BPLUGINS/ZX3
         BIN/ZXUNOCFG

4. Rename SYS/NMI.SYS as SYS/NMI.ORG

5. Download Bob Fossil's NMI browser from
   <http://www.thefossilrecord.co.uk/wp-content/uploads/zx/BROWSE_latest.zip>
   and copy at least these files and directories:

         BIN/BROWSE
         BIN/BROWSE.BIN
         BIN/NMIINIT
         BIN/BPLUGINS/
         SYS/NMI.SYS

6. Follow the installation steps indicated at the beginning of this text

### What is inside the file AUTOBOOT_xxx.BAS?

Just a BASIC program with this content:

        10 .zxunocfg -s3:BORDER 7:PAPER 7:INK 0:CLS
        20 IF INKEY$ ="z" OR INKEY$ ="Z" THEN GO TO 60
        30 .cd <path>
        40 .zxunocfg -s0:.browse
        50 STOP
        60 .zxunocfg -s0:.128
        70 STOP
      9999 SAVE *"AUTOBOOT.BAS"LINE 10

where *path* is either /cores, /cores/bit or /cores/zxx3

...and autoboot on line 10

---

## Castellano

### Hardware necesario

- ZXTRES, ZXTRES+ o ZXTRES++ (se necesita tarjeta intermedia -middle board-
  para la carga de ficheros BIT)
- Tarjeta microSD

*NOTA:* Se recomienda tener instalado como core principal el de Spectrum EXP28
090923, así como, para el uso de la la tarjeta intermedia, bootstrap v1.03 o
posterior, USB v01.02 o posterior y MIDI v01.08 o posterior.

### Software necesario

- [esxdos](http://esxdos.org) compatible con la versión instalada en SPI flash
  (la más reciente en este momento es la 0.8.9)
- Comando "dot" zxunocfg (disponible en [los repositorios oficiales de ZXTRES](https://github.com/zxtres/dot_commands/tree/main/zxunocfg)
- [Navegador NMI de Bob Fossil](http://www.thefossilrecord.co.uk/wp-content/uploads/zx/BROWSE_latest.zip)
- Plugin BIT y/o ZX3 instalado en BIN/BPLUGINS/BIT

### Instalación

1. Editar /SYS/CONFIG/ESXDOS.CFG y poner AutoBoot=1
2. Según donde se desee dejar los ficheros de core (/CORES, /CORES/BIT o
   /CORES/ZX3), copiar en la tarjeta  el fichero correspondiente, con el
   programa con autoarranque, renombrado como /SYS/AUTOBOOT.BAS
3. Entrar en los ajustes avanzados de BIOS y poner velocidad 8X, y en Main la
   pausa de inicio a 0 (Disabled)
4. Copiar los ficheros BIT y/o ZX3 a utilizar dentro dell directorio elegido
   en el paso 2

### Cómo crear una microSD desde cero

1. Formatear usando FAT32

   Para tarjetas del tamaño adecuado (32GB o menos para FAT32), se puede utilizar
   la [herramienta de formateo oficial de la SD Association](https://www.sdcard.org/downloads/formatter/)

   Si es en macOS, además puede ser útil también usar estos comandos después para
   que el sistema no indexe la tarjeta, y no haya papelera al borrar archivos.

         mdutil -i off /Volumes/<nombre de microSD>
         cd /Volumes/<nombre de microSD>
         dot_clean . -n && find . -name ".DS*" -exec rm {} \;
         cd -

2. Descargar esxdos: <http://esxdos.org> y copiar en la tarjeta los directorios
   BIN, SYS y TMP

3. Descargar las utilidades para ZXTRES desde
   <https://github.com/zxdos/zxuno/tree/master/SD/BIN> y
   <https://github.com/zxtres/dot_commands/> y copiar, al menos, los ficheros
   siguientes(aunque se recomienda usar todos):

         BIN/BPLUGINS/BIT
         BIN/BPLUGINS/MID
         BIN/BPLUGINS/ZX3
         BIN/ZXUNOCFG

4. Renombrar SYS/NMI.SYS como SYS/NMI.ORG

5. Descargar el navegador NMI de Bob Fossil desde
   <http://www.thefossilrecord.co.uk/wp-content/uploads/zx/BROWSE_latest.zip>
   y copiar estos ficheros y directorios:

         BIN/BROWSE
         BIN/BROWSE.BIN
         BIN/NMIINIT
         BIN/BPLUGINS/
         SYS/NMI.SYS

6. Seguir los pasos de instalación indicados al principìo de este texto

### ¿Qué hay en el fichero AUTOBOOT_xxx.BAS?

Se trata de un programa BASIC con este contenido:

        10 .zxunocfg -s3:BORDER 7:PAPER 7:INK 0:CLS
        20 IF INKEY$ ="z" OR INKEY$ ="Z" THEN GO TO 60
        30 .cd <ruta>
        40 .zxunocfg -s0:.browse
        50 STOP
        60 .zxunocfg -s0:.128
        70 STOP
      9999 SAVE *"AUTOBOOT.BAS"LINE 10

Donde *ruta* es /cores, /cores/bit o bien /cores/zx3

...y autoarranque en la línea 10

---

## License

BSD 2-Clause License

Copyright (c) 2023, kounch
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

- Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

- Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
