/** Measure callback and handler lifetimes without replacing the production module. */
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {resolve} = require('node:path');
const {test} = require('node:test');
const vm = require('node:vm');
const source = readFileSync(resolve(__dirname, '../../../../web_portal/static/js/operation_results.js'), 'utf8');

/** Build only the browser scheduling boundary used by the result module. */
class ResultHarness {
    constructor() {
        this.frames = new Map();
        this.timers = new Map();
        this.requests = [];
        this.observers = new Set();
        this.resize = new Set();
        this.fonts = new Set();
        this.elements = new Map();
        this.nextId = 0;
        this.context = vm.createContext(this.globals());
        vm.runInContext(source, this.context);
        this.results = this.context.OperationResults;
    }

    element(id) {
        if (!this.elements.has(id)) {
            const classes = new Set(['d-none']);
            this.elements.set(id, {
                innerHTML: '', textContent: '', value: '',
                classList: {add: value => classes.add(value), remove: value => classes.delete(value)},
                setAttribute() {}, querySelector() { return null; }
            });
        }
        return this.elements.get(id);
    }

    globals() {
        const harness = this;
        return {
            escapeHtml: value => String(value),
            readJsonAnswer: value => value,
            document: {
                getElementById: id => this.element(id), querySelectorAll: () => [],
                fonts: {
                    addEventListener: (_, listener) => this.fonts.add(listener),
                    removeEventListener: (_, listener) => this.fonts.delete(listener)
                }
            },
            window: {
                addEventListener: (_, listener) => this.resize.add(listener),
                removeEventListener: (_, listener) => this.resize.delete(listener)
            },
            ResizeObserver: class {
                constructor(callback) { this.callback = callback; harness.observers.add(this); }
                observe() {}
                disconnect() { harness.observers.delete(this); }
            },
            requestAnimationFrame: callback => { const id = ++this.nextId; this.frames.set(id, callback); return id; },
            cancelAnimationFrame: id => this.frames.delete(id),
            setTimeout: callback => { const id = ++this.nextId; this.timers.set(id, callback); return id; },
            clearTimeout: id => this.timers.delete(id),
            fetch: url => new Promise((accept, reject) => this.requests.push({url, accept, reject}))
        };
    }

    async answer(index = this.requests.length - 1, extra = {}) {
        this.requests[index].accept({
            columns: ['state'], rows: [['up']], total_rows: 1, total_pages: 1, page: 1, ...extra
        });
        await new Promise(setImmediate);
    }

    paint() {
        const callbacks = [...this.frames.values()];
        this.frames.clear();
        callbacks.forEach(callback => callback());
    }
}

test('reset cancels frames, observers, resize handlers, font handlers, and search timers', async () => {
    const harness = new ResultHarness();
    harness.results.showForRun(['Adjacency.csv']);
    await harness.answer();
    assert.equal(harness.frames.size, 1);
    harness.results.onSearchInput('old');
    assert.equal(harness.timers.size, 1);
    harness.results.reset();
    for (const resource of [harness.frames, harness.timers, harness.observers, harness.resize, harness.fonts]) {
        assert.equal(resource.size, 0);
    }
});

test('repeated data and layout changes retain one handler and one scheduled frame', async () => {
    const harness = new ResultHarness();
    for (let index = 0; index < 5; index++) {
        harness.results.showForRun(['Adjacency.csv']);
        await harness.answer();
        harness.resize.forEach(callback => { callback(); callback(); });
        assert.equal(harness.frames.size, 1);
        assert.equal(harness.observers.size, 1);
        assert.equal(harness.resize.size, 1);
        assert.equal(harness.fonts.size, 1);
        harness.paint();
        assert.equal(harness.frames.size, 0);
    }
    harness.results.reset();
});

test('a stale response after reset cannot restore result data or a warning', async () => {
    const harness = new ResultHarness();
    harness.results.showForRun(['Old.csv']);
    harness.results.reset();
    await harness.answer(0, {sort_truncated: true, sort_limit: 50000});
    assert.equal(harness.element('resultsBody').innerHTML, '');
    assert.equal(harness.frames.size, 0);
    assert.equal(harness.observers.size, 0);
});

test('a newer file rejects older success and error callbacks', async () => {
    const harness = new ResultHarness();
    harness.results.showForRun(['Old.csv']);
    harness.results.selectFile('Error.csv');
    harness.results.selectFile('New.csv');
    await harness.answer(2, {sort_truncated: true, sort_limit: 50000});
    harness.paint();
    const current = harness.element('resultsTruncated').innerHTML;
    assert.match(current, /50000 rows only/);
    await harness.answer(0);
    harness.requests[1].reject(new Error('old failure'));
    await new Promise(setImmediate);
    assert.equal(harness.element('resultsTruncated').innerHTML, current);
    assert.match(harness.element('resultsBody').innerHTML, /up/);
    harness.results.reset();
});

test('an empty run cancels the active search and all layout work', async () => {
    const harness = new ResultHarness();
    harness.results.showForRun(['Old.csv']);
    await harness.answer();
    harness.results.onSearchInput('old');
    harness.results.showForRun([]);
    assert.equal(harness.timers.size, 0);
    assert.equal(harness.frames.size, 0);
    assert.equal(harness.observers.size, 0);
});

test('changing files cancels a previous filter before it can fetch again', async () => {
    const harness = new ResultHarness();
    harness.results.showForRun(['Old.csv']);
    await harness.answer();
    harness.results.onSearchInput('old');
    harness.results.selectFile('New.csv');
    assert.equal(harness.timers.size, 0);
    assert.match(harness.requests[1].url, /New.csv/);
    assert.equal(harness.requests.length, 2);
    harness.results.reset();
    await harness.answer();
    assert.equal(harness.observers.size, 0);
});
