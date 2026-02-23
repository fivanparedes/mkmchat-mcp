<?php

namespace App\Livewire\Admin;

use App\Models\LlmModel;
use Livewire\Component;
use Livewire\WithPagination;

class LlmModels extends Component
{
    use WithPagination;

    /* ------------------------------------------------------------------ */
    /*  Search / filter                                                    */
    /* ------------------------------------------------------------------ */
    public string $search = '';

    public function updatedSearch(): void
    {
        $this->resetPage();
    }

    /* ------------------------------------------------------------------ */
    /*  Create / Edit form state                                           */
    /* ------------------------------------------------------------------ */
    public bool   $showForm      = false;
    public ?int   $editingId     = null;
    public string $name          = '';
    public string $slug          = '';
    public string $parameterSize = '';
    public string $provider      = 'ollama';
    public string $description   = '';
    public bool   $isActive      = true;

    /* ------------------------------------------------------------------ */
    /*  Delete confirmation                                                */
    /* ------------------------------------------------------------------ */
    public bool $confirmingDelete = false;
    public ?int $deletingId       = null;

    /* ------------------------------------------------------------------ */
    /*  Actions                                                            */
    /* ------------------------------------------------------------------ */

    public function openCreate(): void
    {
        $this->resetForm();
        $this->showForm = true;
    }

    public function openEdit(int $id): void
    {
        $model = LlmModel::findOrFail($id);

        $this->editingId     = $model->id;
        $this->name          = $model->name;
        $this->slug          = $model->slug;
        $this->parameterSize = $model->parameter_size ?? '';
        $this->provider      = $model->provider;
        $this->description   = $model->description ?? '';
        $this->isActive      = $model->is_active;
        $this->showForm      = true;
    }

    public function save(): void
    {
        $rules = [
            'name'          => ['required', 'string', 'max:255'],
            'slug'          => ['required', 'string', 'max:255', 'unique:llm_models,slug,' . ($this->editingId ?? 'NULL')],
            'parameterSize' => ['nullable', 'string', 'max:20'],
            'provider'      => ['required', 'string', 'max:50'],
            'description'   => ['nullable', 'string', 'max:1000'],
            'isActive'      => ['boolean'],
        ];

        $validated = $this->validate($rules);

        $data = [
            'name'           => $this->name,
            'slug'           => $this->slug,
            'parameter_size' => $this->parameterSize ?: null,
            'provider'       => $this->provider,
            'description'    => $this->description ?: null,
            'is_active'      => $this->isActive,
        ];

        if ($this->editingId) {
            LlmModel::findOrFail($this->editingId)->update($data);
            session()->flash('status', 'Model updated.');
        } else {
            LlmModel::create($data);
            session()->flash('status', 'Model created.');
        }

        $this->resetForm();
    }

    public function confirmDelete(int $id): void
    {
        $this->confirmingDelete = true;
        $this->deletingId       = $id;
    }

    public function delete(): void
    {
        if ($this->deletingId) {
            LlmModel::findOrFail($this->deletingId)->delete();
            session()->flash('status', 'Model deleted.');
        }

        $this->confirmingDelete = false;
        $this->deletingId       = null;
    }

    public function cancelDelete(): void
    {
        $this->confirmingDelete = false;
        $this->deletingId       = null;
    }

    public function toggleActive(int $id): void
    {
        $model = LlmModel::findOrFail($id);
        $model->update(['is_active' => ! $model->is_active]);
    }

    /* ------------------------------------------------------------------ */
    /*  Helpers                                                            */
    /* ------------------------------------------------------------------ */

    private function resetForm(): void
    {
        $this->showForm      = false;
        $this->editingId     = null;
        $this->name          = '';
        $this->slug          = '';
        $this->parameterSize = '';
        $this->provider      = 'ollama';
        $this->description   = '';
        $this->isActive      = true;
        $this->resetValidation();
    }

    /* ------------------------------------------------------------------ */
    /*  Render                                                             */
    /* ------------------------------------------------------------------ */

    public function render()
    {
        $models = LlmModel::query()
            ->when($this->search, fn ($q) => $q->where('name', 'like', "%{$this->search}%")
                ->orWhere('slug', 'like', "%{$this->search}%"))
            ->orderBy('name')
            ->paginate(10);

        return view('livewire.admin.llm-models', compact('models'));
    }
}
