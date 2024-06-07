from qtsymbols import *
import os, functools
import gobject
from myutils.config import globalconfig, _TRL
from gui.inputdialog import autoinitdialog_items, noundictconfigdialog1, autoinitdialog
from gui.usefulwidget import (
    D_getsimplecombobox,
    D_getspinbox,
    makescrollgrid,
    D_getcolorbutton,
    yuitsu_switch,
    D_getsimpleswitch,
)


def showvoicelist(self, vl, idx):
    try:
        self.voicecombo.blockSignals(True)
        self.voicecombo.clear()
        self.voicecombo.addItems(vl)
        if idx >= 0:
            self.voicecombo.setCurrentIndex(idx)
        self.voicecombo.blockSignals(False)
    except:
        self.voicecombo_cache = vl, idx


def changevoice(self, text):

    globalconfig["reader"][gobject.baseobject.reader_usevoice]["voice"] = (
        gobject.baseobject.reader.voicelist[self.voicecombo.currentIndex()]
    )


def createvoicecombo(self):

    self.voicecombo = QComboBox()
    self.voicecombo.currentTextChanged.connect(lambda x: changevoice(self, x))
    try:
        vl, idx = self.voicecombo_cache
        self.voicecombo.addItems(vl)
        if idx >= 0:
            self.voicecombo.setCurrentIndex(idx)
    except:
        pass
    return self.voicecombo


def setTab5(self, l):
    makescrollgrid(setTab5lz(self), l)


def getttsgrid(self):

    grids = []
    i = 0
    self.ttswitchs = {}
    line = []
    for name in globalconfig["reader"]:

        _f = "./LunaTranslator/tts/{}.py".format(name)
        if os.path.exists(_f) == False:
            continue
        if "args" in globalconfig["reader"][name]:
            items = autoinitdialog_items(globalconfig["reader"][name])
            items[-1]["callback"] = gobject.baseobject.startreader
            _3 = D_getcolorbutton(
                globalconfig,
                "",
                callback=functools.partial(
                    autoinitdialog,
                    self,
                    globalconfig["reader"][name]["name"],
                    800,
                    items,
                ),
                icon="fa.gear",
                constcolor="#FF69B4",
            )

        else:
            _3 = ""

        line += [
            ((globalconfig["reader"][name]["name"]), 6),
            (
                D_getsimpleswitch(
                    globalconfig["reader"][name],
                    "use",
                    name=name,
                    parent=self,
                    callback=functools.partial(
                        yuitsu_switch,
                        self,
                        globalconfig["reader"],
                        "ttswitchs",
                        name,
                        gobject.baseobject.startreader,
                    ),
                    pair="ttswitchs",
                ),
                1,
            ),
            _3,
        ]
        if i % 3 == 2:
            grids.append(line)
            line = []
        else:
            line += [""]
        i += 1
    if len(line):
        grids.append(line)
    return grids


def setTab5lz(self):

    grids = getttsgrid(self)
    grids += [
        [],
        [("选择声音", 6), (functools.partial(createvoicecombo, self), 15)],
        [
            ("语速:(-10~10)", 6),
            (D_getspinbox(-10, 10, globalconfig["ttscommon"], "rate"), 3),
        ],
        [
            ("音量:(0~100)", 6),
            (D_getspinbox(0, 100, globalconfig["ttscommon"], "volume"), 3),
        ],
        [("自动朗读", 6), (D_getsimpleswitch(globalconfig, "autoread"), 1)],
        [("不被打断", 6), (D_getsimpleswitch(globalconfig, "ttsnointerrupt"), 1)],
        [
            ("朗读原文", 6),
            (D_getsimpleswitch(globalconfig, "read_raw"), 1),
            "",
            "",
            ("朗读翻译", 6),
            (D_getsimpleswitch(globalconfig, "read_trans"), 1),
        ],
        [
            ("朗读的翻译", 6),
            (
                D_getsimplecombobox(
                    _TRL(
                        [
                            globalconfig["fanyi"][x]["name"]
                            for x in globalconfig["fanyi"]
                        ]
                    ),
                    globalconfig,
                    "read_translator",
                ),
                15,
            ),
        ],
        [],
        [
            ("语音修正", 6),
            D_getsimpleswitch(globalconfig["ttscommon"], "tts_repair"),
            D_getcolorbutton(
                globalconfig,
                "",
                callback=lambda x: noundictconfigdialog1(
                    self,
                    globalconfig["ttscommon"],
                    "tts_repair_regex",
                    "语音修正",
                    ["正则", "原文", "替换"],
                ),
                icon="fa.gear",
                constcolor="#FF69B4",
            ),
        ],
    ]
    return grids
