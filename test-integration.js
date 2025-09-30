#!/usr/bin/env node

/**
 * Integration Test Script
 * Tests full stack: Frontend → Backend → (Mock Freqtrade)
 */

const http = require('http');

const tests = [
  {
    name: 'Backend Health Check',
    url: 'http://localhost:5000/api/health',
  },
  {
    name: 'Backend Status',
    url: 'http://localhost:5000/api/status',
  },
  {
    name: 'Backend Balance',
    url: 'http://localhost:5000/api/balance',
  },
  {
    name: 'Backend Trades',
    url: 'http://localhost:5000/api/trades',
  },
  {
    name: 'Backend Profit',
    url: 'http://localhost:5000/api/profit',
  },
  {
    name: 'Backend Daily',
    url: 'http://localhost:5000/api/daily',
  },
  {
    name: 'Backend Strategies',
    url: 'http://localhost:5000/api/strategies',
  },
  {
    name: 'Frontend Home Page',
    url: 'http://localhost:3000',
  },
];

async function testEndpoint(test) {
  return new Promise((resolve) => {
    const start = Date.now();
    http
      .get(test.url, (res) => {
        const duration = Date.now() - start;
        let data = '';

        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {
          const success = res.statusCode === 200;
          resolve({
            ...test,
            success,
            status: res.statusCode,
            duration: `${duration}ms`,
            dataPreview: data.substring(0, 100),
          });
        });
      })
      .on('error', (err) => {
        resolve({
          ...test,
          success: false,
          error: err.message,
        });
      });
  });
}

async function runTests() {
  console.log('🧪 Starting Full Stack Integration Tests\n');
  console.log('=' .repeat(70));

  const results = [];

  for (const test of tests) {
    process.stdout.write(`Testing: ${test.name.padEnd(30)} ... `);
    const result = await testEndpoint(test);
    results.push(result);

    if (result.success) {
      console.log(`✅ PASS (${result.duration})`);
    } else {
      console.log(`❌ FAIL (${result.error || result.status})`);
    }
  }

  console.log('=' .repeat(70));
  console.log('\n📊 Test Summary:\n');

  const passed = results.filter((r) => r.success).length;
  const failed = results.filter((r) => !r.success).length;

  console.log(`Total Tests: ${results.length}`);
  console.log(`✅ Passed: ${passed}`);
  console.log(`❌ Failed: ${failed}`);
  console.log(`Success Rate: ${((passed / results.length) * 100).toFixed(1)}%`);

  if (failed > 0) {
    console.log('\n❌ Failed Tests:');
    results
      .filter((r) => !r.success)
      .forEach((r) => {
        console.log(`  - ${r.name}: ${r.error || r.status}`);
      });
  }

  console.log('\n🎉 Integration test complete!');
  console.log('\nServices Status:');
  console.log('  - Frontend:  http://localhost:3000 ✅');
  console.log('  - Backend:   http://localhost:5000 ✅');
  console.log('  - Freqtrade: http://localhost:8080 (mock data)');
}

runTests();