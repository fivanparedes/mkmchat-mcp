<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class ChatPageTest extends TestCase
{
    use RefreshDatabase;

    public function test_chat_page_is_reachable_for_verified_authenticated_users(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)->get(route('chat'));

        $response
            ->assertOk()
            ->assertSee('Chat', false);
    }

    public function test_guest_is_redirected_from_chat_page(): void
    {
        $response = $this->get(route('chat'));

        $response->assertRedirect(route('login'));
    }

    public function test_main_navigation_includes_chat_link(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)->get(route('dashboard'));

        $response
            ->assertOk()
            ->assertSee(route('chat'), false)
            ->assertSee(__('Chat'), false);
    }
}
