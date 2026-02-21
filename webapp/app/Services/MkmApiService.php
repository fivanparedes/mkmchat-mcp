<?php

namespace App\Services;

use Illuminate\Http\Client\ConnectionException;
use Illuminate\Support\Facades\Http;
use RuntimeException;

class MkmApiService
{
    private string $baseUrl;

    public function __construct()
    {
        $this->baseUrl = rtrim(config('mkm.api_url', 'http://localhost:8080'), '/');
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
    public function suggestTeam(string $strategy, array $ownedCharacters = []): array
    {
        $payload = ['strategy' => $strategy];

        if (!empty($ownedCharacters)) {
            $payload['owned_characters'] = array_values(array_filter(
                array_map('trim', $ownedCharacters)
            ));
        }

        try {
            // LLM inference can be slow — suspend the execution time limit for this call.
            set_time_limit(0);

            $response = Http::timeout(600)
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

        // The Python server wraps the payload in a "response" key.
        if (!isset($body['response'])) {
            throw new RuntimeException('Unexpected API response shape: missing "response" key.');
        }

        return $body['response'];
    }

    public function askQuestion(string $question): string
    {
        $payload = ['question' => $question];

        try {
            set_time_limit(0);

            $response = Http::timeout(600)
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

        return (string) $body['response'];
    }
}
