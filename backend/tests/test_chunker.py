from app.services.chunker import chunk_text


text = """
Our company provides technical support to customers.

Customers can contact support by email or through
the support dashboard.

Refund requests must be submitted within 30 days
of the original purchase.

Enterprise customers receive priority support.

Support is available Monday through Friday.
"""


chunks = chunk_text(
    text,
    chunk_size=100,
    overlap=20,
)

print("Number of chunks:", len(chunks))

for index, chunk in enumerate(chunks):
    print()
    print(f"--- Chunk {index} ---")
    print(chunk)