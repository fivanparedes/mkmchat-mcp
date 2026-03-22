<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class MechanicPageTest extends TestCase
{
    use RefreshDatabase;

    public function test_mechanic_page_is_reachable_for_verified_authenticated_users(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)->get(route('mechanic'));

        $response
            ->assertOk()
            ->assertSee('Explain a Mechanic', false);
    }

    public function test_main_navigation_includes_explain_mechanic_link(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)->get(route('dashboard'));

        $response
            ->assertOk()
            ->assertSee(route('mechanic'), false)
            ->assertSee(__('Explain mechanic'), false);
    }
}
