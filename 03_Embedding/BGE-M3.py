
from FlagEmbedding import BGEM3FlagModel

# 定义主方法
def main():
    
    # 指定模型
    model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=False)
    # demo数据
    text = ["猢狲施展烈焰拳，击退妖怪；随后开启金刚体，抵挡神兵攻击。"]

    # 编码文本
    embeddings = model.encode(
        sentences = text,
        return_dense=True,
        return_sparse=True,
        return_colbert_vecs=True
    )
    
    print("向量后的具体内容:", embeddings)
    
    # 提取向量
    
    # 输出打印
    
    
    
# 定义文件主入口    
if __name__ == "__main__":
    main()