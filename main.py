#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  ama_parse.py
#
#  Copyright 2014 Alexei Krivtsov <kralole@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#
#  Эта программа является свободным программным обеспечением; вы можете
#  распространять и/или изменять в соответствии с условиями GNU General
#  Public License, опубликованной Free Software Foundation; либо
#  версии 2 Лицензии, либо (по вашему выбору) любой более поздней версии.
#
#  Эта программа распространяется в надежде, что она будет полезной,
#  но БЕЗ ВСЯКИХ ГАРАНТИЙ; даже без подразумеваемой гарантии
#  или ПРИГОДНОСТИ ДЛЯ КОНКРЕТНЫХ ЦЕЛЕЙ. Смотрите
#  GNU General Public License для более подробной информации.
#
#  ----------------------------------------------------------------
#
#  Парсинг CDR файлов детализации с АТС si3000.
#  Описание структуры бинарного файла: FUN559000-EDE-060
#


import parse
import os

ama_files = os.listdir('./ama')

with open('cdr.csv', 'w') as csv_file:
    for i in ama_files:
        print i
        list_record = parse.parse_ama('./ama/' + i)
        for call in list_record:
            csv_file.write(call + '\n')
            print call
    csv_file.close()
