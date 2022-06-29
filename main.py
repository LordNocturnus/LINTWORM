from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, FigureCanvasAgg
from matplotlib.figure import Figure
from datetime import datetime
import PySimpleGUI as sg
import numpy as np
import pandas as pd
import os

from code_pieces import Code
import parser


def window_start(theme="DarkRed2", path=None, graph="abs", report=False):

    sg.theme(theme)

    if not path:
        path = sg.popup_get_folder('Folder/file to check')

    if path:
        paths = [[path]]
        progress = [[0, 1]]
        data = [[0], [0], [0], [0]]

        layout = [[sg.Canvas(size=(640, 480), key='-CANVAS-')],
                  [sg.Text('Checking: ', key="text")],
                  [sg.Sizer(80, 1), sg.ProgressBar(100, orientation='h', size=(38.14, 20), k='PBAR')]]

        window = sg.Window("LINTWORM", layout, finalize=True)
        pbar = window["PBAR"]

        fig = Figure()
        ax = fig.add_subplot(111)
        ax.set_ylabel("Passing [%]")
        ax.set_xlabel("Progress [%]")
        ax.set_xlim([0, 100])
        ax.grid()
        figure_agg = FigureCanvasTkAgg(fig, window['-CANVAS-'].TKCanvas)
        figure_agg.draw()
        figure_agg.get_tk_widget().pack(side='top', fill='both', expand=1)

        while True:
            event, values = window.read(timeout=0.1)
            if event == sg.WIN_CLOSED:
                window.close()
                break
            if len(progress) >= 1 and not progress[0][0] == progress[0][1]:
                progress, res, data = file_iterator(paths[-1][progress[-1][0]], progress, data, report)
                if res:
                    paths.append(res)

                while progress[-1][0] == progress[-1][1] and not len(progress) == 1:
                    progress.pop(-1)
                    if len(progress) < len(paths):
                        paths.pop(-1)
                    progress[-1][0] += 1
                pbar.update(prog_calc(progress))

                data[0][-1] = prog_calc(progress)
                ax.cla()
                ax.grid()
                ax.set_xlim([0, 100])
                if graph == "abs":
                    ax.plot(data[0], data[1], label="files")
                    ax.plot(data[0], data[2], label="functions/classes")
                    ax.plot(data[0], data[3], label="commented")
                elif graph == "percent":
                    percent = np.zeros(np.asarray(data[3]).shape, dtype="float")
                    percent[np.asarray(data[2]) != 0] += np.asarray(data[3])[np.asarray(data[2]) != 0] /\
                                                         np.asarray(data[2])[np.asarray(data[2]) != 0] * 100
                    ax.plot(data[0], percent, label="files")
                ax.legend(loc='upper left')
                figure_agg.draw()

                try:
                    if len(paths[-1][progress[-1][0]]) > 75:
                        window["text"].update(f"Checking: {paths[-1][progress[-1][0]][:75]}...")
                    else:
                        window["text"].update(f"Checking: {paths[-1][progress[-1][0]]}")
                except IndexError:
                    pass


def simple_start(path, report=None):
    if report:
        report = report + "/LintwormReport_" + datetime.now().strftime("%H_%M_%S") + ".csv"
    paths = [[path]]
    progress = [[0, 1]]
    data = [[0], [0], [0], [0]]

    while len(progress) >= 1 and not progress[0][0] == progress[0][1]:
        progress, res, data = file_iterator(paths[-1][progress[-1][0]], progress, data, report)
        if res:
            paths.append(res)

        while progress[-1][0] == progress[-1][1] and not len(progress) == 1:
            progress.pop(-1)
            if len(progress) < len(paths):
                paths.pop(-1)
            progress[-1][0] += 1


def file_iterator(path, progress, data, report=None):
    data[0].append(data[0][-1])
    if os.path.isfile(path):
        progress[-1][0] += 1
        paths = None

        if path[-3:] == ".py":
            res = analyse_file(path, report)
            data[1].append(data[1][-1] + 1)
            data[2].append(data[2][-1] + res[0])
            data[3].append(data[3][-1] + res[1])

        else:
            data[1].append(data[1][-1])
            data[2].append(data[2][-1])
            data[3].append(data[3][-1])
    else:
        paths = []
        progress.append([0, len([f for f in os.scandir(path)])])
        for f in os.scandir(path):
            paths.append(f.path)
        data[1].append(data[1][-1])
        data[2].append(data[2][-1])
        data[3].append(data[3][-1])

    return progress, paths, data


def prog_calc(progress):
    prog_float = 0.0
    segment = 100
    for p in progress:
        segment = segment / p[1]
        prog_float += segment * p[0]
    return prog_float


def analyse_file(path, report=None):
    f = open(path, "r").readlines()
    data = [0, 0]
    lines = []
    for line in f:
        if "\t" in line:
            line = parser.replace_tabs(line)
        lines.append([len(line) - len(line.lstrip(' ')), line])

    code = Code("__main__", -1, path)
    code.parse(0, lines)
    code.check()
    if report:
        try:
            df = pd.read_csv(report)
        except OSError:
            df = pd.DataFrame([], columns=["path", "name", "type", "start_line", "end line", "inputs", "returns",
                                           "raises", "basic comments", "multiline comments", "formatted multiline",
                                           "Documented"])
        df = code.report(df)
        df.to_csv(report, index=False)
    print(f"finished file {path}")

    return data


if __name__ == "__main__":
    #window_start(path="G:/pythonprojects/NEST/LINTWORM", graph="percent", report=True)
    simple_start(path="G:/pythonprojects/NEST/WIZARD", report="G:/pythonprojects/NEST/LINTWORM")
