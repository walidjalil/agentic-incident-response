#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 10:33:01 2026

@author: walidajalil
"""

import pathlib
from incident_tools import search_logs

HADOOP_DIR = pathlib.Path(__file__).parent / "datasets/loghub/hadoop/full"
# LABEL_FILE = HADOOP_DIR / "abnormal_label.txt"


result = search_logs(
    application_id="application_1445062781478_0011",
    query=None,
    limit=1000,
)


def load_labels():
    docs = []
    for txt_file in HADOOP_DIR.glob("abnormal_label.txt"):
        with open(txt_file) as f:
            docs.append(
                {
                    "source": txt_file.name,
                    "text": f.readlines(),
                }
            )
    return docs


result_labels = load_labels()
