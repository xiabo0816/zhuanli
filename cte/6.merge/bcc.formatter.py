# -*- coding: utf-8 -*-
import os
import argparse
import json

def get_args_parser():
    parser = argparse.ArgumentParser(description='输入bcc分析结果，输出json格式')
    parser.add_argument('-i', '--input', default='bcc.gbk',
                        type=str, help='输入的bcc分析结果，gbk编码')
    parser.add_argument('-o', '--output', default='input/bcc.utf8.json',
                        type=str, help='输出json格式的bcc分析结果，utf8编码')
    return parser.parse_args()

def run(args):
    result = {}
    gongkaihao = ''
    with open(args.input, 'r', encoding='gbk', errors='ignore') as fin:
        lines = fin.readlines()
        for line in lines:
            # if line[0:3] == '<#>':
            #     gongkaihao = line[3:].strip()
            #     result[gongkaihao] = {}
            # else:
            #     [leixing, zhi] = line.strip().split('_', 1)
            #     if leixing not in result[gongkaihao]:
            #         result[gongkaihao][leixing] = []
            #     result[gongkaihao][leixing].append(zhi)
    
            # if line[0:3] == '<#>':
            #     gongkaihao = line[3:].strip()
            #     result[gongkaihao] = []
            # else:
            #     [location, feature] = line.strip().split('_', 1)
            #     result[gongkaihao].append({"feature": feature,"location": location})
                
            if line[0:3] == '<#>':
                gongkaihao = line[3:].strip()
                result[gongkaihao] = {}
            else:
                [location, feature] = line.strip().split('_', 1)
                if location not in result[gongkaihao]:
                    result[gongkaihao][location] = []
                result[gongkaihao][location].append({"feature": feature,"location": location})

    with open(args.output, 'w', encoding='UTF-8') as fout:
        fout.write(json.dumps(result))

if __name__ == '__main__':
    args = get_args_parser()
    print(args)
    run(args)