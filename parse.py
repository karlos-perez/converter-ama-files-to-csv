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
#  Принимает адрес файла и парсит его. Возвращает список соединений.
#  Описание структуры бинарного файла: FUN559000-EDE-060
#

import struct
import datetime
import os


def get_bytes_len(tetr_len):
    ''' Длина кода зоны и номера'''
    if (tetr_len % 2) == 0:
        tetr_len /= 2
    else:
        tetr_len = tetr_len / 2 + 1
    return tetr_len


def get_bcd(data, lac_len):
    ''' Расшифровка Двоично-десятичной записи (BCD) '''
    result = ""
    pos = 0
    bpos = 0
    while pos < lac_len:
        part = data[bpos]
        bpos += 1
        f = struct.unpack('B', part)
        result += str((f[0] & 0b11110000) >> 4)
        pos += 1

        if pos < lac_len:
            result += str((f[0] & 0b00001111))
            pos += 1
    return result


def get_fields(data, var_len):
    ''' Получение данных о соединении '''
    pos = 0
    result = {}
    while pos < var_len:
        part = data[pos]
        f = struct.unpack('B', part)

        # Вызываемый номер
        # Called number
        if f[0] == 100:
            part = data[pos+1]
            num_len = struct.unpack('B', part)
            bytes_num_len = get_bytes_len(num_len[0])
            num = get_bcd(data[pos+2:(pos + 2 + bytes_num_len)], num_len[0])
            result[100] = num
            #print num
            pos += 2 + bytes_num_len

        # Номер абонента, на которого передан вызов
        # Call accepting party number
        elif f[0] == 101:
            part = data[pos+2]
            num_len = struct.unpack('B', part)
            bytes_num_len = get_bytes_len(num_len[0])
            num = get_bcd(data[pos+3:(pos + 3 + bytes_num_len)], num_len[0])
            result[101] = num
            #print "num 101 = %s" % num
            pos += 3 + bytes_num_len

        # Дата и время начала вызова
        # Start date and time
        elif f[0] == 102:
            #print "f[0] == 102"
            part = data[pos+1:(pos+1+7)]
            result['START_TIME_RAW'] = part
            start_time = get_time(part)
            result[102] = start_time
            pos += 9

        # Дата и время завершения вызова
        # End date and time
        elif f[0] == 103:
            #print "f[0] == 103"
            part = data[pos+1:(pos+1+7)]
            result['STOP_TIME_RAW'] = part
            stop_time = get_time(part)
            result[103] = stop_time
            pos += 9

        else:
            #print "No code pos= %s -- %s\n" % (pos, f[0])
            break
    return result


def get_time(param):
    '''
    Дата и время вызова
    0 - year (0-99)
    1 - month (1-12)
    2 - day (1-31)
    3 - hour (0-23)
    4 - minute (0-59)
    5 - second (0-59)
    6 - 100 ms (0-9)
    '''
    f = struct.unpack('7B', param)
    result = "%.2d.%.2d.20%d %.2d:%.2d:%.2d" % (f[2], f[1], f[0], f[3],
                                                f[4], f[5])
    return result



def get_duration(start, stop):
    '''Получение длительности вызова'''
    fstart = struct.unpack('BBBBBBB', start)
    fstop = struct.unpack('BBBBBBB', stop)

    date_start = datetime.datetime(fstart[0], fstart[1], fstart[2],
                                   fstart[3], fstart[4], fstart[5])
    date_stop = datetime.datetime(fstop[0], fstop[1], fstop[2],
                                  fstop[3], fstop[4], fstop[5])
    duration = date_stop - date_start
    return duration.seconds


def parse_ama(file_ama):
    ''' Парсинг бинарного ama файла '''
    record_list = []
    fn = open(file_ama, 'rb')
    file_size = os.stat(file_ama)[6]
    size = 0
    while size < file_size:
        #print size, ' --- ', file_size
        data = fn.read(1)
        f = struct.unpack('B', data)
        #print "f = %s" % f
        if f[0] == 200:
            # 2 - record len (bin)
            # 8 - call id (bin)
            # 3 - flags (bin)
            # 1 - posled(4bit), rezerv(4bit) (bin)
            # 1 - lac_len(3bit), spis_num_len(5bit) (bin)
            # sum = 15
            data = fn.read(15)
            f = struct.unpack('!H8sBBBBB', data)
            record_len = f[0]  # длина записи
            lac_len = (f[6] & 0b11100000) >> 5  # Длина кода зоны
            spis_num_len = (f[6] & 0b00011111)  # Длина абонентского номера
            bytes_lac_len = get_bytes_len(lac_len)
            bytes_spis_num_len = get_bytes_len(lac_len + spis_num_len)
            size += record_len
            #print "record_len = %s" % record_len
            #print "bytes_lac_len = %s" % bytes_spis_num_len
            #print "bytes_spis_num_len = %s" % bytes_spis_num_len
            
            if spis_num_len > 0:
                data = fn.read(bytes_spis_num_len)
                spis_num_len = lac_len + spis_num_len
                spis_num = get_bcd(data, spis_num_len)
                #print "spis_num = %s" % spis_num
            var_len = record_len - 16 - bytes_lac_len - bytes_spis_num_len
            #print "var_len = %s" % var_len
            data = fn.read(var_len)
            fields = get_fields(data, var_len)
            duration = get_duration(fields['START_TIME_RAW'],
                                    fields['STOP_TIME_RAW'])

            if spis_num != '':
                number_from = spis_num
                number_to = fields[100]
                start_date = fields[102]
                log_record = "%s;%s;%s;%s" % (start_date, number_from,
                                              number_to, duration)
                #print log_record
                record_list.append(log_record)

        # Запись об изменении даты и времени
        # Record at date and time changes
        elif f[0] == 210:
            record_list.append('Date and time change;;;')
            size += 16
            #print "Date and time change\n"

        # Запись о потере определенного количества записей
        # Record on the loss of a certain amount of records
        elif f[0] == 211:
            record_list.append('Lost records found;;;')
            size += 19
            #print "Lost records found\n"

        # Запись о перезапуске CS
        # CS restart record
        elif f[0] == 212:
            record_list.append('Reboot CS record;;;')
            size += 12
            #print "Reboot CS record\n"

        else:
            record_list.append('Record parse error. Unknow record %s;;;'  % f[0])
            #print "Record parse error. Unknow record %s \n" % f[0]
    fn.close()
    return record_list
