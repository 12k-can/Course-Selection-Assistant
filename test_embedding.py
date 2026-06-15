from sentence_transformers import SentenceTransformer

print("开始加载模型...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

print("模型加载成功")

vec = model.encode("什么是通识选修课")

print("向量长度:", len(vec))
print(vec[:5])