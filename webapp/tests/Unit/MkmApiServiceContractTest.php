<?php

namespace Tests\Unit;

use App\Services\MkmApiService;
use Illuminate\Support\Facades\Http;
use RuntimeException;
use Tests\TestCase;

class MkmApiServiceContractTest extends TestCase
{
    public function test_chat_response_contract_is_parsed(): void
    {
        config()->set('mkm.api_url', 'http://python-api:8080');

        Http::fake([
            'http://python-api:8080/chat' => Http::response([
                'response' => [
                    'text' => 'Answer in markdown',
                    'summary_text' => 'Compacted summary',
                    'summary_message_count' => 12,
                ],
            ], 200),
        ]);

        $service = app(MkmApiService::class);
        $result = $service->chat('hello', [['role' => 'user', 'content' => 'hello']], null, 0, 'llama3.2:3b');

        $this->assertSame('Answer in markdown', $result['text']);
        $this->assertSame('Compacted summary', $result['summary_text']);
        $this->assertSame(12, $result['summary_message_count']);
    }

    public function test_suggest_team_requires_response_envelope(): void
    {
        config()->set('mkm.api_url', 'http://python-api:8080');

        Http::fake([
            'http://python-api:8080/suggest-team' => Http::response([
                'char1' => ['name' => 'Missing envelope'],
            ], 200),
        ]);

        $service = app(MkmApiService::class);

        $this->expectException(RuntimeException::class);
        $this->expectExceptionMessage('missing "response" key');

        $service->suggestTeam('aggressive', [], 'llama3.2:3b');
    }
}
