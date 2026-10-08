import assert from 'node:assert/strict';
import {test} from 'node:test';
import {metadata} from './validate-skills.mjs';
const doc = (fields,body='Instructions') => `---\n${fields}\n---\n${body}`;
test('single-line metadata preserves quoted description and invocation policy',()=>{
  assert.deepEqual(metadata(doc('name: sample\ndescription: "Use: a sample"\ndisable-model-invocation: true'),'test'),{name:'sample',description:'Use: a sample','disable-model-invocation':'true'});
});
test('malformed metadata fails before running models',()=>{
  for (const text of [doc('name: sample\ndescription: |\n  multiline'),doc('name: sample\ndescription: sample\nname: other'),doc('name: Sample\ndescription: sample'),doc('name: sample\ndescription: sample\ndisable-model-invocation: yes'),doc('name: sample\ndescription: sample','')]) assert.throws(()=>metadata(text,'test'));
});
