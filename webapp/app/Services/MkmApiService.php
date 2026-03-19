<?php

namespace App\Services;

use Illuminate\Http\Client\ConnectionException;
use Illuminate\Http\Client\PendingRequest;
use Illuminate\Support\Facades\Http;
use RuntimeException;

class MkmApiService
{
    private string $baseUrl;
    private ?string $apiKey;
    private string $apiKeyHeader;

    public function __construct()
    {
        $this->baseUrl = rtrim(config('mkm.api_url', 'http://localhost:8080'), '/');
        $apiKey = config('mkm.api_key');
        $this->apiKey = is_string($apiKey) && trim($apiKey) !== '' ? trim($apiKey) : null;
        $header = config('mkm.api_key_header', 'X-API-Key');
        $this->apiKeyHeader = is_string($header) && trim($header) !== '' ? trim($header) : 'X-API-Key';
    }

    /**
     * Call the Python /suggest-team endpoint.
     *
     * @param  string        $strategy         The user's strategy text.
     * @param  array<string> $ownedCharacters  Optional list of owned character names.
     * @return array  The decoded response body (keys: char1, char2, char3, strategy).
     *
     * @throws RuntimeException  On connection failure or error response from the API.
     */
    public function suggestTeam(string $strategy, array $ownedCharacters = [], ?string $model = null): array
    {
        $payload = ['strategy' => $strategy];

        if (!empty($ownedCharacters)) {
            $payload['owned_characters'] = array_values(array_filter(
                array_map('trim', $ownedCharacters)
            ));
        }

        if ($model) {
            $payload['model'] = $model;
        }

        try {
            // LLM inference can be slow — suspend the execution time limit for this call.
            set_time_limit(0);

            $response = $this->httpRequest()->timeout(600)
                ->post("{$this->baseUrl}/suggest-team", $payload);
        } catch (ConnectionException $e) {
            throw new RuntimeException(
                'Cannot reach the MK Mobile assistant API. Make sure the Python server is running.',
                0,
                $e
            );
        }

        $body = $response->json();

        // Handle explicit error responses from the Python server.
        if ($response->failed() || isset($body['error'])) {
            $message = $body['error'] ?? "API returned HTTP {$response->status()}";
            if (isset($body['raw_response'])) {
                $message .= ' (raw LLM output could not be parsed as JSON)';
            }
            throw new RuntimeException($message);
        }

        if (!isset($body['response'])) {
            throw new RuntimeException('Unexpected API response shape: missing "response" key.');
        }

        $team = $this->normalizeTeamResponse($body['response']);

        if (!$this->hasVisibleTeamContent($team)) {
            throw new RuntimeException('API returned success but no team content was provided.');
        }

        return $team;
    }

    public function askQuestion(string $question, ?string $model = null): string
    {
        $payload = ['question' => $question];

        if ($model) {
            $payload['model'] = $model;
        }

        try {
            set_time_limit(0);

            $response = $this->httpRequest()->timeout(600)
                ->post("{$this->baseUrl}/ask-question", $payload);
        } catch (ConnectionException $e) {
            throw new RuntimeException(
                'Cannot reach the MK Mobile assistant API. Make sure the Python server is running.',
                0,
                $e
            );
        }

        $body = $response->json();

        if ($response->failed() || isset($body['error'])) {
            throw new RuntimeException($body['error'] ?? "API returned HTTP {$response->status()}");
        }

        if (!isset($body['response'])) {
            throw new RuntimeException('Unexpected API response shape: missing "response" key.');
        }

        $text = $this->normalizeTextResponse($body['response']);

        if ($text === '') {
            throw new RuntimeException('API returned success but no answer text was provided.');
        }

        return $text;
    }

    /**
     * @param  mixed  $response
     * @return array<string, mixed>
     */
    private function normalizeTeamResponse(mixed $response): array
    {
        if (is_array($response)) {
            if (isset($response['response']) && is_array($response['response'])) {
                $response = $response['response'];
            }

            if (isset($response['text']) && !isset($response['strategy'])) {
                $response['strategy'] = (string) $response['text'];
            }

            return $response;
        }

        if (is_string($response) && trim($response) !== '') {
            $decoded = json_decode($response, true);
            if (is_array($decoded)) {
                return $this->normalizeTeamResponse($decoded);
            }

            return ['strategy' => trim($response)];
        }

        return [];
    }

    /**
     * @param  array<string, mixed>  $team
     */
    private function hasVisibleTeamContent(array $team): bool
    {
        if (trim((string) ($team['strategy'] ?? '')) !== '') {
            return true;
        }

        foreach (['char1', 'char2', 'char3'] as $key) {
            if (!isset($team[$key]) || !is_array($team[$key])) {
                continue;
            }

            if (trim((string) ($team[$key]['name'] ?? '')) !== '') {
                return true;
            }
        }

        return false;
    }

    private function normalizeTextResponse(mixed $response): string
    {
        if (is_string($response)) {
            return trim($response);
        }

        if (is_array($response)) {
            if (isset($response['response'])) {
                return $this->normalizeTextResponse($response['response']);
            }

            if (isset($response['text']) && is_string($response['text'])) {
                return trim($response['text']);
            }
        }

        return '';
    }

    private function httpRequest(): PendingRequest
    {
        $request = Http::acceptJson();

        if ($this->apiKey !== null) {
            $request = $request->withHeaders([
                $this->apiKeyHeader => $this->apiKey,
            ]);
        }

        return $request;
    }
}
