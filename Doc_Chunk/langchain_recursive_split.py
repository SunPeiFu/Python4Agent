from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 加载读取文档
loader = TextLoader("90-文档-Data/山西文旅/云冈石窟.txt")
documents = loader.load()

# 按照换行符 逗号 点句号 空格切分
separators = ["\n\n", ",", "."," "]
# 构造切分器
recursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
    chunk_size = 100,
    chunk_overlap = 15,
    separators = separators
)

docs = recursiveCharacterTextSplitter.split_documents(documents)

for i, doc in enumerate(docs):
    print("当前index:",i)
    print("当前的pagecontent:",doc.page_content)
    print("-"*100)
    
# 输出结果示例:
"""
当前index: 0
当前的pagecontent: 云冈石窟
云冈石窟位于中国北部山西省大同市西郊17公里处的武周山南麓，石窟依山开凿，东西绵延1公里。存有主要洞窟45个，大小窟龛252个，石雕造像51000余躯，为中国规模最大的古代石窟群之一，与敦煌莫高窟、洛阳龙门石窟和天水麦积山石窟并称为中国四大石窟艺术宝库。
--------------------------------------------------
当前index: 1
当前的pagecontent: 1961年被国务院公布为全国首批重点文物保护单位，2001年12月14日被联合国教科文组织列入世界遗产名录，2007年5月8日被国家旅游局评为首批国家5A级旅游景区。
--------------------------------------------------
当前index: 2
当前的pagecontent: 云冈五华洞
位于云冈石窟中部的第
--------------------------------------------------
当前index: 3
当前的pagecontent: 9——13窟。这五窟因清代施泥彩绘云冈石窟景观而得名。五华洞雕饰绮丽，丰富多彩，是研究北魏历史、艺术、音乐、舞蹈、书法和建筑的珍贵资料，为云冈石窟群的重要组成部分。
--------------------------------------------------
"""    