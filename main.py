import pandas as pd
from openai import OpenAI
import json
import os


DEEPSEEK = 1


file_path = 'data.xlsx'
df = pd.read_excel(file_path, header=None)
data_list = df.values.tolist()
print("单词组数量：", len(data_list))

latex = [
        r"\documentclass[12pt]{article}",
        r"\usepackage[UTF8]{ctex}",
        r"\usepackage{amsmath, amssymb}",
        r"\usepackage{geometry}",
        r"\geometry{a4paper, margin=1in}",
        r"\usepackage{enumitem}",
        r"\usepackage{xcolor}",
        r"\usepackage{titlesec}",
        r"\usepackage{multicol}",
        r"\titleformat{\section}{\large\bfseries\color{blue}}{}{0em}{}",
        r"\titleformat{\subsection}{\normalsize\bfseries\color{black}}{}{0em}{}",
        r"\begin{document}",
        r"\usepackage{fontspec}",
        r"\setmainfont{Charis SIL}"
    ]

if DEEPSEEK:
    # 创建目录
    os.makedirs("json_file", exist_ok=True)

    # deepseek设置
    token = "sk-c796bd521b9141c3a819b9aef1f356da"
    client = OpenAI(
        api_key=token,
        base_url="https://api.deepseek.com",
    )
    system_prompt = """
    用户会提供一组含义相近的单词，用逗号分隔。请你将每个单词、音标及其汉语意思、一到三个例句、与其它单词的辨析输出为JSON文件。
    
    EXAMPLE INPUT: 
    start,commence
    
    EXAMPLE JSON OUTPUT:
    {
        "start": { "pronunciation": "",
                   "meaning": { "vt.vi.": "开始；发动；开办；以…起家",
                                "vi.": "出发，启程；（从…）开始",
                                "n.": "开端；开始"},
                   "sentence": ["The meeting started at 9 a.m."],
                 },
        "commence": { "pronunciation": "",
                      "meaning": { "vt.vi.": "开始；着手"},
                      "sentence": ["OK, let the journey commence."],
                    },
        "_difference_": { "语体风格不同": { "start": "常用、口语化、中性，适用于日常表达和多数写作场景。",
                                        "commence": "正式、书面化，常见于官方、公文、学术或法律语言中。" },
                          "搭配对象不同": { "start": "可以用于广泛的动词搭配，如 start a car, start studying, start to cry 等。",
                                        "commence": "commence 一般用于较正式的活动、过程，如 commence a ceremony, commence operations, commence proceedings。"}
                        }
        
    }
    """

    for group in data_list:
        # 发送请求
        user_prompt = " "
        for word in group:
            user_prompt += word + ","
        print("用户请求：" ,user_prompt[:-1])
        messages = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}]

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            response_format={
                'type': 'json_object'
            }
        )

        # 获取json数据
        json_file = json.loads(response.choices[0].message.content)

        # 获取比对单词
        all_word = ""
        for word in json_file.keys():
            if word != "_difference_":
                all_word += word + "-"
        latex.append((r"\section*{" + all_word)[:-1] + "}")
        latex.append("\\begin{multicols}{2}")
        print(data_list.index(group) + 1 ,all_word[:-1], "生成JSON及LaTex文件...")

        # 保存为JSON文件
        filename = f"{all_word[:-1]}.json"
        with open(f"json_file/{filename}", "w", encoding="utf-8") as f:
            json.dump(json_file, f, ensure_ascii=False, indent=4)

        # 生成LaTeX代码
        for word, content in json_file.items():
            if word != "_difference_":
                latex.append(f"\subsection*{{\\textbf{{{word}}}\\quad{content['pronunciation']}}}")
                if "meaning" in content:
                    latex.append(r"\begin{itemize}[leftmargin=2em]")
                    for pos, definition in content["meaning"].items():
                        latex.append(f"\item[{pos}] {definition}")
                    latex.append(r"\end{itemize}")
                if "sentence" in content:
                    latex.append(r"\textbf{例句：}")
                    latex.append(r"\begin{itemize}[leftmargin=2em]")
                    for s in content["sentence"]:
                        latex.append(f"\item {s}")
                    latex.append(r"\end{itemize}")
            else:
                latex.append("\end{multicols}")
                for diff_type, diff_detail in content.items():
                    latex.append(f"\subsection*{{{diff_type}}}")
                    latex.append(r"\begin{itemize}")
                    for k, v in diff_detail.items():
                        latex.append(f"\item[\\textbf{{{k}}}] {v}")
                    latex.append(r"\end{itemize}")
    latex.append(r"\end{document}")
    latex_code = "\n".join(latex)

    # 保存为LaTeX文件
    with open("vocab_comparison.tex", "w", encoding="utf-8") as f:
        f.write(latex_code)
