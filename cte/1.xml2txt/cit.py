# -*- coding: utf-8 -*-

from lxml import etree
import lxml
import argparse
import os
import argparse
from tqdm import tqdm
import time
import threading
import regex
from io import StringIO, BytesIO


def get_args_parser():
    parser = argparse.ArgumentParser(description='XML citation parser')
    parser.add_argument('-i', '--input', default='citation',
                        type=str, help='input folder')
    parser.add_argument('-o', '--output', default='citation_out',
                        type=str, help='output folder')
    parser.add_argument('-n', '--nfiles', default=8,
                        type=int, help='输出nfiles份文件，默认是8')
    return parser.parse_args()


# https://www.w3school.com.cn/xpath/xpath_syntax.asp
def get_publicid(root):
    return ''.join(root.xpath('//business:PublicationReference[@dataFormat="standard"]/base:DocumentID/*[position()<4]/text()', namespaces=root.nsmap))


def get_publicdate(root):
    return ''.join(root.xpath('//business:PublicationReference[@dataFormat="standard"]/base:DocumentID/base:Date/text()', namespaces=root.nsmap))


def get_ipc(root):
    ipc_old = ''.join(root.xpath(
        '//business:ClassificationIPC/*[@dataFormat="original"][position()<2]/text()', namespaces=root.nsmap))
    ipc_new = ''.join(root.xpath(
        '//business:ClassificationIPCR[position()<2]/*[position()>1][position()<6]/text()', namespaces=root.nsmap))
    return ipc_old + ipc_new


def get_title(root):
    return ''.join(root.xpath('//business:InventionTitle/text()', namespaces=root.nsmap))


def get_abstract(root):
    return ''.join(root.xpath('//business:Abstract//base:Paragraphs/text()', namespaces=root.nsmap))


def get_claims(root):
    return ''.join(root.xpath('//business:Claims//business:ClaimText/text()', namespaces=root.nsmap))


def get_descriptions(root):
    return ''.join(root.xpath('//business:Description//base:Paragraphs//text()', namespaces=root.nsmap))


def run(filename):
    # https://lxml.de/
    # file coding: UTF-8
    result = []
    try:
        root = etree.parse(BytesIO(open(filename, 'rb').read()),
                           etree.XMLParser(ns_clean=True)).getroot()
        result.append(get_publicid(root))
        result.append(get_title(root))
        result.append(get_publicdate(root))
        result.append(get_ipc(root))
        result.append(get_abstract(root))
        result.append(get_claims(root))
        result.append(get_descriptions(root))
        return result
    except Exception:
        print('Error(1) Xml parsing, at file:'+filename)
        return False


def strB2Q(ustring):
    rstring = ''
    # https://www.regular-expressions.info/unicode.html
    ustring = regex.sub(
        r'[^\p{Han}\p{Letter}\p{Number}\p{Punctuation}]+', '', ustring)
    ustring = regex.sub(r'[—]+', '-', ustring)

    # ustring = re.sub(r'[^\p{Han}\p{Letter}\p{Number}\p{Pd}\p{Ps}\p{Pe}\p{Pi}\p{Pf}\p{Pc}]+', '', ustring)
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 0x28:
            inside_code += 65248
        elif inside_code == 0x29:
            inside_code += 65248
        elif inside_code == 0x5B:
            inside_code += 65248
        elif inside_code == 0x5D:
            inside_code += 65248
        elif inside_code == 0x3A:
            inside_code += 65248
        elif inside_code == 0x3B:
            inside_code += 65248
        rstring += chr(inside_code)
    return rstring


def cut_text(text, length):
    text_list = regex.findall(r'.{'+str(length)+r'}', text)
    text_list.append(text[(len(text_list)*length):])
    return text_list


def _sent_tokenize(parah):
    sents = [strB2Q(sent) for sent in regex.split(r'(。|！|\!|？|\?)', parah)]
    sents.append("")
    sents = ["".join(i) for i in zip(sents[0::2], sents[1::2])]

    results = []
    for sent in sents:
        if len(sent) > 0:
            results.extend(cut_text(sent, 500))

    results = [r.strip('\x5C') for r in results if not r ==
               '' and not r == '\x5c' and not r == '。']
    return "\n".join(results)


def _t_writefile(input_folder, output_folder, inputfilelist, pbar, docid):
    print(input_folder, output_folder, inputfilelist, pbar, docid)
    with open(os.path.join(output_folder, str(docid)) + '_out', 'w', encoding='UTF-8') as fout:
        for item in inputfilelist:
            text = run(item)
            publicid = text[0]
            title = text[1]
            time = text[2]
            ipc = text[3]
            abstract = text[4]
            claim = text[5]
            description = text[6]

            html = ''
            html += '<#>%d PublicId=%s;Cat=%s;Time=%s\n' % (
                docid, publicid, _sent_tokenize(ipc), time)
            html += '<p>title\n%s\n</p>\n' % (_sent_tokenize(title).strip())
            html += '<p>abstract\n%s\n</p>\n' % (
                _sent_tokenize(abstract).strip())
            html += '<p>claim\n%s\n</p>\n' % (_sent_tokenize(claim).strip())
            html += '<p>description\n%s\n</p>\n' % (
                _sent_tokenize(description).strip())
            html += '</#>\n'

            fout.write(html)
            docid += 1
            pbar.update(1)
    fout.close()

# 为线程定义一个函数


class writeFileThread (threading.Thread):
    def __init__(self, threadID, input_folder, output_folder, inputfilelist, pbar, docid):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.inputfilelist = inputfilelist
        self.docid = docid
        self.pbar = pbar

    def run(self):
        _t_writefile(self.input_folder, self.output_folder,
                     self.inputfilelist, self.pbar, self.docid)


def _listdir(rootDir, affix):
    names = []
    for filename in os.listdir(rootDir):
        pathname = os.path.join(rootDir, filename)
        if os.path.isfile(pathname):
            if filename.lower().endswith(affix):
                names.append(pathname)
        else:
            names.extend(_listdir(pathname, affix))
    return names


if __name__ == '__main__':
    args = get_args_parser()
    print(args)
    filelist = _listdir(args.input, 'xml')
    print('total files: ' + str(len(filelist)))

    n_thread = args.nfiles if len(filelist) > args.nfiles else len(filelist)
    with tqdm(total=len(filelist)) as pbar:
        threads = []
        # 创建新线程
        length = len(filelist)
        size = int(len(filelist)/n_thread)

        for i in range(0, length, size):
            threads.append(writeFileThread(1, args.input,
                                           args.output, filelist[i:i+size], pbar, i))
        # 开启新线程
        for t in threads:
            t.start()
        for t in threads:
            t.join()
