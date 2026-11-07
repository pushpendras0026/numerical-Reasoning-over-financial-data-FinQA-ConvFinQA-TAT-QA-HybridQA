import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import os
import re
from lxml.html.clean import Cleaner
import json


def clean_html(raw_html):
    cleaner = Cleaner(remove_tags=["sup"])
    return cleaner.clean_html(raw_html).decode("utf-8")

EMPTY = "[EMPTY]"

def isYear(value):
    for i in range(1990, 2022):
        if str(i) in value:
            return True
    return False

def existTopHeaders(html):
    first_row = html.tr
    if first_row.td.string == None:
        return True

    for td in first_row.find_all("td"):
        if not td.string:
            continue
        value = td.string.replace(",", "").strip()
        if value:
            try:
                float(value[1:])
                if isYear(value):
                    return True
                else:
                    return False
            except:
                continue
    return True

def belongToTopHeaders(row):
    for i, td in enumerate(row.find_all("td")):
        if not td.string:
            continue
        value = td.string.replace(",", "").strip()
        if value:
            try:
                float(value[1:])
                if isYear(value):
                    return True
                else:
                    return False
            except:
                continue
    return True

def handle_unnamed_single_topheader(columns, j):
    tmp = j
    while tmp < len(columns) and (columns[tmp].startswith("Unnamed") or columns[tmp] == EMPTY):
        tmp += 1
    if tmp < len(columns):
        return columns[tmp]
    
    tmp = j
    while tmp >= 0 and (columns[tmp].startswith("Unnamed") or columns[tmp] == EMPTY):
        tmp -= 1
    if tmp < 0:
        return f"data {j}"
    else:
        return columns[tmp]

def handle_unnamed_multi_topheader(columns, j):
    tmp = j
    while tmp < len(columns) and (columns[tmp][0].startswith("Unnamed") or columns[tmp][0] == EMPTY):
        tmp += 1
    if tmp < len(columns):
        return columns[tmp][0]
    
    tmp = j
    while tmp >= 0 and (columns[tmp][0].startswith("Unnamed") or columns[tmp][0] == EMPTY):
        tmp -= 1
    if tmp < 0:
        return f"data {j}"
    else:
        return columns[tmp][0]

def readHTML(html_string):
    # file_path = html_path
    html = BeautifulSoup(html_string, features='html.parser')
    # remove superscripts and subscripts
    for sup in html.select('sup'):
        sup.extract()
    for sup in html.select('sub'):
        sup.extract()

    # 1. locate top header
    top_header_nonexist_flag = 0
    if not existTopHeaders(html):
        top_header_nonexist_flag = 1
        new_tr_tag = html.new_tag("tr")
        new_td_tag = html.new_tag("td")
        new_tr_tag.insert(0, new_td_tag)
        for i in range(len(html.tr.find_all("td")[1:])):
            new_td_tag1 = html.new_tag("td")
            new_td_tag1.string = f"data{i}"
            new_tr_tag.insert(i+1, new_td_tag1)
        html.table.insert(0, new_tr_tag)
    else:
        html.tr.td.string = ""

    header = [0] 
    top_header_flag = True
    for i, tr in enumerate(html.find_all("tr")):
        # # for locating top header
        # if tr.td.string and ("in thousands" in tr.td.string.lower() or "in millions" in tr.td.string.lower()) and len(tr.td.string) < len("in thousands") + 5:
        #     tr.td.replace_with(html.new_tag("td"))
        if top_header_flag and i > 0 and not top_header_nonexist_flag:
            if belongToTopHeaders(tr):
                header.append(i)
            else:
                top_header_flag = False
        # for locating left header
        if tr.td.string != None:
            for td in tr.find_all("td")[1:]:
                if td.string == None:
                    td.string = EMPTY

    data = pd.read_html(str(html), header=header, index_col=0)[0]
    return data, header, top_header_nonexist_flag


def generateDescription(data, header, top_header_nonexist_flag):
    describe_dict = {}
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            value = data.iloc[i, j]
            if str(value).startswith("Unnamed") or str(value) == EMPTY or str(value) == "-" or str(value) == u'\u2014':
                continue
            describe = ""
            if pd.isnull(data.index[i]):
                describe += "total"
            else:   
                describe += f"{data.index[i]}"
            temp_i = i - 1
            while temp_i >= 0:
                if (data.iloc[temp_i] == EMPTY).all():
                    describe += f" {data.index[temp_i]}"
                    break
                temp_i -= 1
            if not top_header_nonexist_flag:
                describe += " of"
                if len(header) == 1:
                    describe += f" {handle_unnamed_single_topheader(data.columns, j)}"
                else:
                    describe += f" {handle_unnamed_multi_topheader(data.columns, j)}"
                    prev = handle_unnamed_multi_topheader(data.columns, j)
                    for temp_j in header[1:]:
                        if data.columns[j][temp_j].startswith("Unnamed") or data.columns[j][temp_j] == EMPTY:
                            continue
                        if data.columns[j][temp_j] == prev:
                            continue
                        describe += f" {data.columns[j][temp_j]}"
                        prev = data.columns[j][temp_j]
            describe += f" is {data.iloc[i, j]}."
            x_index = i+len(header)
            y_index = j+1
            if top_header_nonexist_flag == 1:
                x_index -= 1 
            describe_dict[f"{x_index}-{y_index}"] = describe
    return describe_dict

def generateDiscreptionCell(data, header, top_header_nonexist_flag):
    discribe_dict = {}
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            value = data.iloc[i, j]
            if str(value).startswith("Unnamed") or str(value) == "-" or str(value) == "[EMPTY]":
                continue
            discribe = f"{data.iloc[i, j]}"
            x_index = i+len(header)
            y_index = j+1
            if top_header_nonexist_flag == 1:
                x_index -= 1 
            discribe_dict[f"{x_index}-{y_index}"] = discribe
    return discribe_dict