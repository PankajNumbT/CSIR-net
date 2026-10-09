"""Exercise the actual Streamlit widget flows when its runtime is installed."""
import importlib.util
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
AVAILABLE=importlib.util.find_spec('streamlit') is not None

@unittest.skipUnless(AVAILABLE,'Streamlit runtime is not installed in this environment')
class StreamlitFlows(unittest.TestCase):
    def app(self):
        from streamlit.testing.v1 import AppTest
        at=AppTest.from_file(str(ROOT/'streamlit_app.py'),default_timeout=30)
        at.session_state['seed']=42
        at.run()
        self.assertFalse(at.exception)
        return at

    def question(self,qid):
        at=self.app()
        at.selectbox('status').set_value('Solutions ready')
        at.text_input('search').input(qid).run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state['queue'],[qid])
        return at

    def test_single_answer_score_and_learning_panels(self):
        qid='2020-june-26nov-q030';at=self.question(qid)
        at.radio(f'answer_{qid}').set_value('D')
        at.button('submit').click().run()
        self.assertEqual(at.session_state['results'][qid]['points'],3)
        at.button('hint').click().run()
        self.assertEqual(at.session_state['hints'][qid],1)
        at.button('solution').click().run()
        self.assertTrue(any(x.value=='Step-by-step solution' for x in at.subheader))
        at.button('theory').click().run()
        self.assertTrue(any(x.value=='Similar questions' for x in at.subheader))
        self.assertFalse(at.exception)

    def test_multiple_answer_exact_set(self):
        qid='2020-june-26nov-q061';at=self.question(qid)
        at.checkbox(f'answer_{qid}_B').check()
        at.checkbox(f'answer_{qid}_C').check()
        at.button('submit').click().run()
        self.assertEqual(at.session_state['results'][qid]['points'],4.75)
        self.assertFalse(at.exception)

    def test_tracks_papers_and_content_workspace(self):
        at=self.app();at.radio('track').set_value('Statistics').run()
        self.assertTrue(any(x.startswith('Probability') for x in at.selectbox('topic_Statistics').options))
        at.radio('workspace').set_value('Papers').run()
        self.assertTrue(at.dataframe)
        self.assertFalse(at.exception)
        at.radio('workspace').set_value('Question bank').run()
        self.assertTrue(at.dataframe)
        self.assertFalse(at.exception)

    def test_bookmark_and_next_question(self):
        at=self.app();first=at.session_state['queue'][0]
        at.button('bookmark').click().run()
        self.assertIn(first,at.session_state['bookmarks'])
        at.button('next').click().run()
        self.assertEqual(at.session_state['cursor'],1)
        self.assertFalse(at.exception)

if __name__=='__main__':unittest.main()
