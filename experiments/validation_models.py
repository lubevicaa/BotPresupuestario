"""Compare candidate lexical baselines on validation ONLY, not test.
Candidate results are diagnostic; they do not replace the neural model.
"""
import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score,accuracy_score
ROOT=Path(__file__).resolve().parents[1]
corpus=json.loads((ROOT/'data/corpus.json').read_text(encoding='utf8'))
train=[(s,l) for l,g in corpus.items() for s in g['train'][:17]]
val=[(s,l) for l,g in corpus.items() for s in g['train'][17:]]
models={
 'word_1_2':TfidfVectorizer(ngram_range=(1,2)),
 'char_3_5':TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5)),
 'word_char':FeatureUnion([('word',TfidfVectorizer(ngram_range=(1,2))),('char',TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5)))])
}
results=[]
for name, vec in models.items():
 x=vec.fit_transform([s for s,l in train]); y=[l for s,l in train]
 vx=vec.transform([s for s,l in val]); vy=[l for s,l in val]
 for c in (0.5,1.0,4.0,12.0):
  model=LogisticRegression(C=c,max_iter=1000,random_state=42).fit(x,y)
  predicted=model.predict(vx)
  results.append({'features':name,'C':c,'accuracy_validation':round(accuracy_score(vy,predicted),4),'macro_f1_validation':round(f1_score(vy,predicted,average='macro'),4)})
results.sort(key=lambda x:(x['macro_f1_validation'],x['accuracy_validation']),reverse=True)
(ROOT/'resultados'/'experimentos_validacion.json').write_text(json.dumps({'note':'VALIDACION exclusivamente. No usar test para seleccionar. Modelo comparativo no neuronal.','candidates':results},indent=2),encoding='utf8')
print('Top validacion:',results[:5])
