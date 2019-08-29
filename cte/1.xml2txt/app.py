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
import zipfile


def get_args_parser():
    parser = argparse.ArgumentParser(description='XML application parser')
    parser.add_argument('-i', '--input', default='application',
                        type=str, help='input folder')
    parser.add_argument('-o', '--output', default='application_out',
                        type=str, help='output folder')
    parser.add_argument('-n', '--nfiles', default=5,
                        type=int, help='输出nfiles份文件，默认是8')
    return parser.parse_args()


# https://www.w3school.com.cn/xpath/xpath_syntax.asp
# https://lxml.de/
def run(filename):
    # file coding: UTF-8 with BOM
    try:
        root = etree.parse(BytesIO(open(filename, 'rb').read()),
                           etree.XMLParser(ns_clean=True)).getroot()
        claim1 = ''.join(root.xpath('//cn-claims/claim[@num="1"]/claim-text/text()', namespaces=root.nsmap))
        claim2 = ''.join(root.xpath('//cn-claims/claim[@num="2"]/claim-text/text()', namespaces=root.nsmap))
        return [claim1, claim2]
    except Exception:
        print('Error(1) Xml parsing, at file:' + filename)
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

            publicid = 'null'
            time = 'null'
            ipc = 'null'

            html = ''
            html += '<#>%d PublicId=%s;Cat=%s;Time=%s\n' % (docid, publicid, _sent_tokenize(ipc), time)
            html += '<p>claim1\n%s\n</p>\n' % (_sent_tokenize(text[0]).strip())
            html += '<p>claim2\n%s\n</p>\n' % (_sent_tokenize(text[1]).strip())
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


def _unzip_folder(path, prefix):
    filelist = _listdir(path, 'zip')
    with tqdm(total=len(filelist)) as pbar:
        for f in filelist:  
            if os.path.getsize(f) and os.path.basename(f).startswith(prefix):
                zipFile = zipfile.ZipFile(f)
                zipFile.extractall(os.path.dirname(f))
            pbar.update(1)

if __name__ == '__main__':
    args = get_args_parser()
    print(args)

    _unzip_folder(args.input, 'DA')

    filelist = _listdir(args.input, 'xml')
    filelist = [i for i in filelist if os.path.dirname(i).endswith('100001-') and os.path.basename(i)]
    print(filelist)
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
