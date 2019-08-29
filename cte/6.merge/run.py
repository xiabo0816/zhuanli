# -*- coding: utf-8 -*-
import os
import argparse
import configparser
import regex as re
import json

gxuhaozifu = re.compile(r'[\p{Letter}\p{Number}\p{Punctuation}一二三四五六七八九十步骤（）【】①②③④⑤⑥⑦⑧⑨⑩ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+')
greggquanliyaoqiu = re.compile(r'^[\d]+\.[根据权利要求 | 如权利要求1所述的 | 按照权利要求1]')

def get_args_parser():
    parser = argparse.ArgumentParser(description='输入词、句和句群特征，输入引用关系，整理成json格式')
    parser.add_argument('-c', '--config', default='example.ini',
                        type=str, help='配置文件，指定了输入词、句和句群特征，输入引用关系，待审查文献和对比文献的引用关系，引用，被引用，类型')
    parser.add_argument('-o', '--output', default='merged.utf8.json',
                        type=str, help='结果文件夹，一对一个json')

    return parser.parse_args()


def mergeid(mref, publicid):
    res = {}
    res['id'] = publicid
    for id, refid in enumerate(mref[publicid]):
        res['compare' + str(id+1) + '_id'] = refid

    return res


def mergebcc(mbcc, mref, publicid, tag):
    # _retOrNull1(mbcc, publicid, tag)
    # zuida = max(len(msteps['publicid']), )
    # {
    #     "feature": "",
    #     "compare1": {
    #         "feature": "",
    #         "location": ""
    #     },
    # }
    if publicid not in mbcc:
        return []

    res = []
    for item in range(0, 100):

        tmp = {}
        if tag in mbcc[publicid] and item < len(mbcc[publicid][tag]):
            tmp['feature'] = mbcc[publicid][tag][item]['feature']
        else:
            tmp['feature'] = ''

        for cmpid, refid in enumerate(mref[publicid]):
            if refid not in mbcc:
                tmp = {}
                tmp['feature'] = ''
                break
            if tag in mbcc[refid] and item < len(mbcc[refid][tag]):
                tmp['compare' + str(cmpid+1)] = mbcc[refid][tag][item]
            else:
                tmp['compare' + str(cmpid+1)] = ''

        if len(['' for i in tmp if tmp[i] != '']) == 0:
            break
        
        res.append(tmp)

    return res


def run(bcc, bm25, steps, ref, output_folder):
    print(bcc, bm25, steps, ref, output_folder)

    mbcc = json.load(open(bcc, 'r'))
    mbm25 = json.load(open(bm25, 'r'))
    msteps = json.load(open(steps, 'r'))
    mref = json.load(open(ref, 'r'))

    print(type(mbm25), type(msteps), type(mref), type(mbcc))
    
    with open(output_folder, 'w', encoding='UTF-8') as fout:
        for publicid in mref:
            linshi = {}
            linshi['id'] = mergeid(mref, publicid)
            
            linshi['claim1'] = []
            linshi['claim2'] = []

            # linshi['claim1'].extend(mergebm25(mbcc, mref, publicid, 'claim1'))
            # linshi['claim2'].extend(mergebm25(mbcc, mref, publicid, 'claim2'))

            linshi['claim1'].extend(mergebcc(mbcc, mref, publicid, 'claim'))
            linshi['claim2'].extend(mergebcc(mbcc, mref, publicid, 'description'))

            # linshi['claim1'].extend(mergesteps(mbcc, mref, publicid))
            # linshi['claim2'].extend(mergesteps(mbcc, mref, publicid))
            fout.write(json.dumps(linshi)+'\n')

    # for publicid in mref:
    #    print(publicid+':'+mref[publicid]+':\n'+'\n'.join(_retOrNull(mbcc, publicid, 'claim'))+'\n:\n'+'\n'.join(_retOrNull(mbcc, mref[publicid], 'claim')))
    #    print(publicid+':'+mref[publicid]+':\n'+'\n'.join(_retOrNull1(msteps, publicid))+'\n:\n'+'\n'.join(_retOrNull1(msteps, mref[publicid])))
    #    print(publicid+':'+mref[publicid]+':\n'+'\n'.join(_retOrNull(mbcc, publicid, 'claim'))+'\n:\n'+'\n'.join(_retOrNull(mbcc, mref[publicid], 'claim')))
    # with open(args.input, 'r', encoding='UTF-8') as fin:


def _retOrNull1(map, key1, key2=-1):
    if key2 == -1:
        if key1 in map:
            return map[key1]
        else:
            return ''
    else:
        if key1 in map and key2 in map[key1]:
            return map[key1][key2]
        else:
            return ''


if __name__ == '__main__':
    args = get_args_parser()
    print(args)
    config = configparser.ConfigParser()
    config.read(args.config)
    run(config['DEFAULT']['bcc'], config['DEFAULT']['bm25'], config['DEFAULT']['steps'], config['DEFAULT']['ref'], args.output)