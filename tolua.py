#!/usr/bin/python2
# -*- coding: utf-8 -*-
import xlrd
import sys
import os
import re
reload(sys)
sys.setdefaultencoding('utf8')

#region FIELDS
ROOT_DIR = os.getcwd()
LUAOUT_DIR = os.path.join(ROOT_DIR,"Test")
EXCEL_DIR = os.path.join(ROOT_DIR,"xlsx_origin")
FILETYPE = ".xlsx"
LUAFILETYPE = ".lua"
TBASE = {"int":True, "string":True, "float":True}
TBASESWITCH = {
    "int": lambda ds,f,v: save_int_value(ds,f,v),
    "float": lambda ds,f,v: save_float_value(ds,f,v),
    "string": lambda ds,f,v: save_string_vale(ds,f,v),
}
TBASESAPPENDWITCH = {
    "int": lambda ds,f,v: append_int_value(ds,f,v),
    "float": lambda ds,f,v: append_float_value(ds,f,v),
    "string": lambda ds,f,v: append_string_vale(ds,f,v),
}
#endregion

#out lua path
lua_path = "LuaOutPath"
#region COMMON

def value_is_none(value):
    return value == ''

def get_int_value(v):
    return 0 if value_is_none(v) else int(v)

def get_float_value(v):
    return 0.0 if value_is_none(v) else float(v)

def get_string_value(v):
    return '' if value_is_none(v) else str(v)

TBASESGETWITCH = {
    "int": get_int_value,
    "float": get_float_value,
    "string": get_string_value,
}
def save_int_value(ds,f,v):
    ds[f] = get_int_value(v)

def save_float_value(ds,f,v):
    ds[f] = get_float_value(v)

def save_string_vale(ds,f,v):
    ds[f] = get_string_value(v)

def append_int_value(ds,f,v):
    ds.append(get_int_value(v))

def append_float_value(ds,f,v):
    ds.append(get_float_value(v))

def append_string_vale(ds,f,v):
    ds.append(get_string_value(v))

def save_list_vale(ds,f,v,tp):
    data = []
    ds[f] = data
    #处理只填了一个值
    if type(v) == int or type(v) == float:
        TBASESAPPENDWITCH[tp](data,0,v)
    else:
        sl = v.split(';')
        for i, v in enumerate(sl):
            TBASESAPPENDWITCH[tp](data,i,v)

def save_dictionary_vale(ds,f,v,tp1,tp2,dm):
    data = {}
    ds[f] = data
    sdi = v.split(';')
    for i, di in enumerate(sdi):
        if not value_is_none(di):
            skv = di.split(',')
            if len(skv) != 2:raise Exception("Error Dictionary ")
            dkey = TBASESGETWITCH[tp1](skv[0])
            TBASESWITCH[tp2](data,dkey,skv[1])
#endregion

#region FUNCTIONS
def check_types(record,types):
    col_idx = 0
    for value in record:
        if col_idx > 0:
            if not value: raise Exception("第 %d 列没填类型"%(col_idx))
            if col_idx == 1 and value != 'int': raise Exception("first type isnot int")
            elif value in TBASE:
                types.append(str(value.strip()))
            elif value.find('List') != -1:
                tb = re.findall(re.compile(r"<(.*?)>",re.S),value)
                if tb[0] in TBASE:
                    types.append(str(value.strip()))
                else:
                    raise Exception("暂不支持该类型List:%s"%(str(value)))
            elif value.find('Dictionary') != -1:
                tb = re.findall(re.compile(r"<(.*?),(.*?)>",re.S),value)
                for tp in tb[0]:
                    if not tp in TBASE:
                        raise Exception("暂不支持该类型Dictionary:%s"%(str(value)))
                types.append(str(value.strip()))
            else:
                raise Exception("暂不支持该类型:%s"%(str(value)))
        col_idx += 1

def check_fields(record,types,fields):
    col_idx = 0
    for value in record:
        if col_idx > 0:
            if value_is_none(value): raise Exception("第 %d 列字段名为空"%(col_idx))
            if col_idx == 1 and value != 'Id': raise Exception("first Key not Id")
            if value in fields: 
                raise Exception("重复的字段名:%s"%(str(value.strip())))
            fields.append(str(value.strip()))
        col_idx += 1

def make_data(record,types,fields,datas):
    data = {}
    if record[1] == '': return 
    datas[int(record[1])] = data
    for i, tp in enumerate(types):
        if not tp: continue
        if tp in TBASE:
            TBASESWITCH[tp](data,fields[i],record[i + 1])
        elif tp.find('List') != -1:
            tb = re.findall(re.compile(r"<(.*?)>",re.S),tp)
            save_list_vale(data,fields[i],record[i + 1],tb[0])
        elif tp.find('Dictionary') != -1:
            tb = re.findall(re.compile(r"<(.*?),(.*?)>",re.S),tp)
            save_dictionary_vale(data,fields[i],record[i + 1],tb[0][0],tb[0][1],datas)
        else:
            raise Exception("暂不支持该类型:%s"%(tp))  

def make_defalue_value(datas,defalut_values,fields):
    value_refs = {}
    for id,data in datas.items():
        for key,value in data.items():
            if not key in value_refs:
                value_refs[key] = {}
            value2str = str(value)
            if not value2str in value_refs[key]:
                value_refs[key][value2str] = {}
                value_refs[key][value2str]['cnt'] = 1
                value_refs[key][value2str]['value'] = value
            else:
                value_refs[key][value2str]['cnt'] += 1
    for key,vl in value_refs.items():
        if not key in defalut_values:
            defalut_values[key] = {}
            defalut_values[key]['cnt'] = 0
        for _,vi in vl.items():
            curr_cnt = defalut_values[key]['cnt']
            if curr_cnt < vi['cnt']:
                defalut_values[key]['value'] = vi['value']
                defalut_values[key]['cnt'] = vi['cnt']
       

def handle_one_file(dirname, filename):
    basename = filename.replace(FILETYPE,"")
    rpath = os.path.join(dirname,filename)
    
    print("process>>>>>>>>>    " + basename)
    excel = xlrd.open_workbook(rpath)
    tables = excel.sheets()

    if len(tables) == 0:
        raise Exception("file is empty" + basename)
    
    for table in tables:
        rows = table.nrows
        if rows < 4:
            raise Exception(basename + "    content error")
        types,fields = [],[]
        datas,defalut_values = {},{}
        #跳过服务器表
        if table.cell(0, 2).value == "server":
            print("break server cfg >",filename)
            return
        for row_idx in range(rows):
            record = table.row_values(row_idx)
            if row_idx == 1:
                check_types(record,types)   
            if row_idx == 2:
                check_fields(record,types,fields)      
            if row_idx >3:
                make_data(record,types,fields,datas)
        make_defalue_value(datas,defalut_values,fields)
        #TODO 只读第一个table        
        break

    gen_lua_file(basename,datas,fields,defalut_values)    
    
def gen_lua_file(baseName,datas,fields,default_value):
    if not os.path.isdir(LUAOUT_DIR):
        os.makedirs(LUAOUT_DIR)

    outfilepath = os.path.join(LUAOUT_DIR,baseName + LUAFILETYPE)
    outfp = open(outfilepath, "w")
    outfp.write('local keys = {')
    for idx,keyn in enumerate(fields):
        outfp.write('%s = %d,'%(keyn,idx + 1))
    outfp.write('}\n')
    outfp.write('local d = \"__default_value__\"\n')
    outfp.write('local data = { \n')
    for key,value in datas.items():
        outfp.write('\t[%d] = {'%(key))
        for idx,keyn in enumerate(fields):
            dlv = value[keyn]
            if dlv == default_value[keyn]['value']:
                outfp.write('d,')
            else:
                if type(dlv) == int:
                    outfp.write('%d,'%(dlv))
                elif type(dlv) == float:
                    outfp.write('%f,'%(dlv))
                elif type(dlv) == str:
                    outfp.write('\"%s\",'%(dlv))
                elif type(dlv) == list:
                    outfp.write('{')
                    for idx,lv in enumerate(dlv):
                        if type(lv) == str:
                            outfp.write('\"%s\",'%(str(lv)))
                        else:
                            outfp.write('%s,'%(str(lv)))
                    outfp.write('},')
                elif type(dlv) == dict:
                    outfp.write('{')
                    for dk,dv in dlv.items():
                        if type(dv) == str:
                            outfp.write('[\"%s\"] = '%(dk) + "\"" + str(dv) + '\",')
                        else:
                            outfp.write('[\"%s\"] = '%(dk) + str(dv) + ',')
                    outfp.write('},')
        outfp.write('},\n')    

    outfp.write('}\n')    
    outfp.write('local default_value = {\n')
    for k,v in default_value.items():
        outfp.write('\t%s = '%(k))
        dv = v['value']
        if type(dv) == int:
            outfp.write('%d,\n'%(dv))
        elif type(dv) == float:
            outfp.write('%f,\n'%(dv))
        elif type(dv) == str:
            outfp.write('\"%s\",\n'%(dv))
        elif type(dv) == list:
            outfp.write('{')
            for idx,lv in enumerate(dv):
                if type(lv) == str:
                    outfp.write('\"%s\",'%(str(lv)))
                else:
                    outfp.write('%s,'%(str(lv)))
            outfp.write('},\n')
        elif type(dv) == dict:
            outfp.write('{')
            for dk,dv in dv.items():
                if type(dv) == str:
                    outfp.write('[\"%s\"] = '%(dk) + "\"" + str(dv) + '\",')
                else:
                    outfp.write('[\"%s\"] = '%(dk) + str(dv) + ',')
            outfp.write('},\n')
    outfp.write('}\n')

    outfp.write('local mt = {}\n')
    outfp.write('mt.__index = function(t,k)\n')
    outfp.write('\t local key = keys[k]\n')
    outfp.write('\t local value = rawget(t,key)\n')
    outfp.write('\tif value == d then return default_value[k] end\n')
    outfp.write('\treturn value')
    outfp.write('\nend')

    outfp.write('\nmt.__newindex = function(t,k)')
    outfp.write('\t error( \' do not edit config \') end')

    outfp.write('\nmt.metatable = false')

    outfp.write('\nfor _,v in pairs(data) do')
    outfp.write('\n\tsetmetatable(v,mt)')
    outfp.write('\nend')

    outfp.write('\nreturn data')

    outfp.close()

#endregion 

def main():
    for parent, dirnames, filenames in os.walk(EXCEL_DIR):
        for filename in filenames:
            if filename.endswith(FILETYPE):
                handle_one_file(parent, filename)
    print("tolua datatable done")
    # handle_one_file(EXCEL_DIR, "itemsBuy.xlsx")

if __name__ == '__main__':
    main()