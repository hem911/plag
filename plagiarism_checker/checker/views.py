import nltk
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer, util
from django.shortcuts import render
from googleapiclient.discovery import build

nltk.download('punkt')
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# Google API Credentials (REPLACE with your own keys)
GOOGLE_API_KEY = "AIzaSyB-3S5jsGvs6-tcgi2rTfjwMvzdINUErTI"
SEARCH_ENGINE_ID = "82767b0837f6e4688"

def search_google(query):
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        result = service.cse().list(q=query, cx=SEARCH_ENGINE_ID, num=3).execute()

        results = []
        if "items" in result:
            for item in result["items"]:
                results.append({
                    "title": item.get("title", "No Title"),
                    "url": item.get("link", "#"),
                    "snippet": item.get("snippet", "No Snippet Available")
                })
        return results
    except Exception as e:
        print("Google Search Error:", e)
        return []

def check_plagiarism(request):
    if request.method == "POST":
        user_text = request.POST.get("text", "").strip()
        if not user_text:
            return render(request, "checker/index.html", {"error": "Please enter some text."})

        sentences = sent_tokenize(user_text)
        key_sentences = sorted(sentences, key=len, reverse=True)[:3]

        matched_sources = []
        total_similarity = 0.0
        match_count = 0

        for sentence in key_sentences:
            results = search_google(sentence)
            combined_snippets = " ".join([r["snippet"] for r in results])
            embeddings = model.encode([sentence, combined_snippets], convert_to_tensor=True)
            score = util.pytorch_cos_sim(embeddings[0], embeddings[1]).item()
            percent = round(score * 100, 2)

            if percent >= 60:
                matched_sources.append({
                    "sentence": sentence,
                    "similarity": percent,
                    "sources": results
                })
                total_similarity += percent
                match_count += 1

        average_plagiarism = round(total_similarity / match_count, 2) if match_count else 0.0

        return render(request, "checker/index.html", {
            "plagiarism_percentage": average_plagiarism,
            "matched_sources": matched_sources,
            "no_plagiarism": match_count == 0
        })

    return render(request, "checker/index.html")
