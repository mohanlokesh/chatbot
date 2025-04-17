import re
import nltk
import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# Define question words and filler words to handle question variations
QUESTION_WORDS = ['how', 'what', 'where', 'when', 'who', 'why', 'can', 'do', 'is', 'are', 'will', 'should']
FILLER_WORDS = ['i', 'me', 'my', 'mine', 'you', 'your', 'yours', 'please', 'kindly', 'want', 'need', 'would', 'like', 'get', 'tell']
IGNORE_WORDS = ['a', 'an', 'the', 'this', 'that', 'these', 'those', 'to', 'for', 'in', 'on', 'with', 'by', 'at', 'and', 'or', 'but']

def preprocess_text(text):
    """
    Preprocess text for NLP:
    - Convert to lowercase
    - Remove punctuation
    - Remove question words (to focus on keywords)
    - Remove common filler words
    - Lemmatize words
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation
    text = ''.join([char for char in text if char not in string.punctuation])
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords, question words, and filler words
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words and 
              token not in QUESTION_WORDS and 
              token not in FILLER_WORDS and
              token not in IGNORE_WORDS]
    
    # Lemmatize
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    # Handle common substitutions (e.g., 'promocode' vs 'promo code')
    processed_text = ' '.join(tokens)
    processed_text = processed_text.replace('promocode', 'promo code')
    processed_text = processed_text.replace('discount code', 'promo code')
    processed_text = processed_text.replace('coupon', 'promo code')
    processed_text = processed_text.replace('voucher', 'promo code')
    
    return processed_text

def extract_entities(text):
    """Extract entities from text (basic implementation)"""
    entities = {
        'company': [],
        'product': [],
        'issue': [],
        'contact': [],
        'action': []
    }
    
    # Simple pattern matching for companies (very basic)
    company_pattern = r'(company|corp|inc|ltd)'
    if re.search(company_pattern, text.lower()):
        # Find words before company/corp/etc.
        matches = re.findall(r'(\w+)\s+(?:company|corp|inc|ltd)', text.lower())
        entities['company'].extend(matches)
    
    # Simple pattern matching for products
    product_pattern = r'(product|item|service)'
    if re.search(product_pattern, text.lower()):
        matches = re.findall(r'(\w+)\s+(?:product|item|service)', text.lower())
        entities['product'].extend(matches)
    
    # Simple pattern matching for issues
    issue_pattern = r'(problem|issue|error|bug|not working)'
    if re.search(issue_pattern, text.lower()):
        matches = re.findall(r'(\w+)\s+(?:problem|issue|error|bug)', text.lower())
        entities['issue'].extend(matches)
    
    # Simple pattern matching for contact
    contact_pattern = r'(email|phone|contact|call)'
    if re.search(contact_pattern, text.lower()):
        entities['contact'].append('contact_request')
    
    # Detect action words (common verbs in questions)
    action_pattern = r'(find|get|use|apply|track|return|reset|change|cancel|pay)'
    if re.search(action_pattern, text.lower()):
        matches = re.findall(action_pattern, text.lower())
        entities['action'].extend(matches)
    
    return entities

def find_best_matches(query, documents, top_n=5):
    """
    Find the best matches for a query from a list of documents
    using TF-IDF and cosine similarity
    """
    # Create a list with the query and all documents
    all_text = [query] + documents
    
    # Preprocess all text
    preprocessed_text = [preprocess_text(text) for text in all_text]
    
    # Create TF-IDF vectorizer with bi-grams and character n-grams
    # This helps catch variations in phrasing
    vectorizer = TfidfVectorizer(
        analyzer='word',
        ngram_range=(1, 2),      # Use both unigrams and bigrams
        sublinear_tf=True        # Apply sublinear tf scaling (logarithmic)
    )
    tfidf_matrix = vectorizer.fit_transform(preprocessed_text)
    
    # Get query vector (first in the matrix)
    query_vector = tfidf_matrix[0:1]
    
    # Get document vectors (rest of the matrix)
    document_vectors = tfidf_matrix[1:]
    
    # Calculate cosine similarity
    cosine_similarities = cosine_similarity(query_vector, document_vectors).flatten()
    
    # Get indices of top matches
    top_indices = cosine_similarities.argsort()[-top_n:][::-1]
    
    # Return top matches with scores
    top_matches = [(documents[i], cosine_similarities[i]) for i in top_indices]
    
    return top_matches

def calculate_keyword_overlap(query, document):
    """
    Calculate the percentage of keywords that overlap between query and document
    This can be used as a fallback when TF-IDF similarity is low
    """
    # Preprocess both texts
    processed_query = preprocess_text(query)
    processed_doc = preprocess_text(document)
    
    # Convert to sets of words
    query_words = set(processed_query.split())
    doc_words = set(processed_doc.split())
    
    # Calculate overlap
    if not query_words:
        return 0
    
    overlap = len(query_words.intersection(doc_words)) / len(query_words)
    return overlap 