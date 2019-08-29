# -*- coding: utf-8 -*-
import os
import argparse
import regex as re
import json

ggfhgju = ['。', '.', '；']
ggfhgxuhao = ['）','：','、','.','，',',', '-']
ggfhgjieshu = ['；','。']
ggfhgkaishi = ['步骤：', '步骤制成：', '具有以下优点：', '优点为：']
ggref = {}
gdefen = 1000
gzuichangxuhao = 5
gxuhaozifu = re.compile(r'[\p{Letter}\p{Number}\p{Punctuation}一二三四五六七八九十步骤（）【】①②③④⑤⑥⑦⑧⑨⑩ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+')
greggquanliyaoqiu = re.compile(r'^[\d]+\.[根据权利要求 | 如权利要求1所述的 | 按照权利要求1]')

def get_args_parser():
    parser = argparse.ArgumentParser(description='输入语料和引用关系，输出换了行的步骤特征')
    parser.add_argument('-i', '--input', default='cn_cn_citation_1000.utf8',
                        type=str, help='输入的语料，utf8编码，格式未分词bcc')
    parser.add_argument('-r', '--reference', default='cn_cn_citation_1000.ref.utf8',
                        type=str, help='待审查文献和对比文献的引用关系，引用，被引用，类型')
    parser.add_argument('-o', '--output', default='cn_cn_citation_1000.out.utf8',
                        type=str, help='结果文件')
    return parser.parse_args()

def xindema(line):
    if line[0:3] == '<#>':
        return True
    else:
        return False

def zhaokaishi(line):
    # 假设：每行只会出现一次可能的子串
    beixuan = []
    for wawawa in ggfhgkaishi:
        beixuan.append(line.find(wawawa))

    end = -1
    start = -1
    for i in range(len(beixuan)):
        item = beixuan[i]
        if item != -1:
            end = item + len(ggfhgkaishi[i])
            break
    
    if end == -1:
        return start, end
    
    for i in ggfhgju:
        t= line[0:end].rfind(i)
        if t != -1:
            start = t + 1
            break
    
    return start, end


def zhaojieshu(line):
    beixuan = []

    # 找到序号结束符号的每一个位置
    flag = False
    for wawawa in ggfhgxuhao:
        t = line.find(wawawa)
        if t == -1:
            beixuan.append(999)
        else:
            flag = True
            beixuan.append(t)
    
    if not flag:
        return ''

    # 找到最小的序号结束符号的位置
    zuixiao = 0
    for i in range(1, len(beixuan)):
        item = beixuan[i]
        if item < beixuan[zuixiao]:
            zuixiao = i

    result = line[0:beixuan[zuixiao]]

    if result == '\n':
        return ''
    if gxuhaozifu.match(result) == None:
        return ''
    if len(result) > gzuichangxuhao:
        return ''
    
    return result


def zhaoxuhao(zuo, you, i, lines):
    # result 的最终result
    rr = []

    # 处理正好换行说步骤的情况 + 没有正好换行说步骤的
    if lines[i][you:] == '\n':
        i += 1
        kaishi = lines[i]
    else:
        kaishi = lines[i][you:]

    # result的flag
    rf = []
    xuhao = zhaojieshu(kaishi)

    if xuhao != '':
        rf.append(xuhao)
    else:
        return '', i
    rr.append(kaishi)

    while True:
        i += 1
        xuhao = zhaojieshu(lines[i])
        if xuhao == '':
            continue
        elif xiangsima(xuhao, rf[-1]):
            if greggquanliyaoqiu.match(lines[i]) == None:
                rf.append(xuhao)
                rr.append(lines[i])
        else :
            break

    return ''.join(rr), i

def xiangsima(xuhao1, xuhao2):
    changdu = min(len(xuhao1), len(xuhao2))    
    defen = 0

    # 这个打分对英文更友好，很丑陋
    for i in range(changdu):
        defen += abs(ord(xuhao1[i]) - ord(xuhao2[i]))

    if defen > gdefen:
        return False
    else:
        return True

def cunziliao(line):
    # PublicId=CN104539029A;
    # PublicId=([\d\w]+)
    matchObj = re.search( r'PublicId=([\d\w]+)', line, re.M|re.I)
    if matchObj:
        return matchObj.group(1)
    else:
        return False

def run(args):

    result = {}

    with open(args.input, 'r', encoding='UTF-8') as fin:
        lines = fin.readlines()
        ziliao = ''

        for i in range(len(lines)):
            line = lines[i]
            zuo, you = zhaokaishi(line)
            if xindema(line):
                ziliao = cunziliao(line)
            elif zuo != -1 and you != -1:
                xuhao, j = zhaoxuhao(zuo, you, i, lines)
                if i != j and xuhao != '' and len(xuhao) > 50:
                    if ziliao not in result:
                        result[ziliao] = []
                    result[ziliao].append(line[zuo:you]+xuhao)
                    print(ziliao + '\n')
                    print(line[zuo:you] + '\n')
                    print(xuhao)
                    i = j                
            else:
                continue
    
    with open(args.output, 'w', encoding='UTF-8') as fout:
        fout.write(json.dumps(result))


if __name__ == '__main__':
    args = get_args_parser()
    print(args)
    run(args)