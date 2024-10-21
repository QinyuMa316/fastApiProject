import pandas as pd
import json


def list_to_csv(input_list, filename, num_cols=3):
    # 计算行数，保证所有元素都能均匀分布到指定列数
    df = pd.DataFrame([input_list[i:i + num_cols] for i in range(0, len(input_list), num_cols)])

    # 保存为CSV文件
    df.to_csv(filename, index=False, header=False)


if __name__ == '__main__':
    with open('data.json', 'r') as f:
        data = json.load(f)

    # 生成编号后的列表
    input_list = [f'{idx + 1}: {elem.strip()}' for idx, elem in enumerate(data['data'])]

    # 输出为csv文件，自定义列数
    list_to_csv(input_list, 'output.csv', num_cols=4)  # 例如保存为4列
