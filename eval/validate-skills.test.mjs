import assert from 'node:assert/strict';
import {test} from 'node:test';
import {metadata, validateInvocationPolicy} from './validate-skills.mjs';
const doc = (fields,body='Instructions') => `---\n${fields}\n---\n${body}`;
test('single-line metadata preserves quoted description and invocation policy',()=>{
  assert.deepEqual(metadata(doc('name: sample\ndescription: "Use: a sample"\ndisable-model-invocation: true'),'test'),{name:'sample',description:'Use: a sample','disable-model-invocation':'true'});
});
test('malformed metadata fails before running models',()=>{
  for (const text of [doc('name: sample\ndescription: |\n  multiline'),doc('name: sample\ndescription: sample\nname: other'),doc('name: Sample\ndescription: sample'),doc('name: sample\ndescription: sample\ndisable-model-invocation: yes'),doc('name: sample\ndescription: sample','')]) assert.throws(()=>metadata(text,'test'));
});
test('host invocation policies agree for explicit-only and automatic skills',()=>{
  validateInvocationPolicy({}, '', 'default');
  validateInvocationPolicy({}, 'policy:\n  allow_implicit_invocation: true\n', 'automatic');
  validateInvocationPolicy({'disable-model-invocation':'true'}, 'interface:\n  display_name: "Test"\npolicy:\n  allow_implicit_invocation: false # explicit only\n', 'manual');
  assert.throws(()=>validateInvocationPolicy({}, 'policy:\n  allow_implicit_invocation: false\n', 'mismatch'), /invocation mismatch/);
  assert.throws(()=>validateInvocationPolicy({'disable-model-invocation':'true'}, '', 'mismatch'), /invocation mismatch/);
  assert.throws(()=>validateInvocationPolicy({}, 'policy:\n  allow_implicit_invocation: "false"\n', 'invalid'), /must be boolean/);
  assert.throws(()=>validateInvocationPolicy({}, 'policy:\n  allow_implicit_invocation: true\n  allow_implicit_invocation: false\n', 'duplicate'), /duplicate/);
  assert.throws(()=>validateInvocationPolicy({}, 'policy: {allow_implicit_invocation: false}\n', 'inline'), /block form/);
  assert.throws(()=>validateInvocationPolicy({}, 'policy:\n  allow_implicit_invocation: true\npolicy:\n  allow_implicit_invocation: true\n', 'duplicate'), /duplicate policy/);
  validateInvocationPolicy({'disable-model-invocation':'true'}, 'policy:\n# manual invocation\n  allow_implicit_invocation: false\ninterface:\n  display_name: "Test"\n', 'comment');
});
