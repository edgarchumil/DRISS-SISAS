import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { MedicationService } from '../core/medication.service';

@Component({
  selector: 'app-medication-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './medication-form.component.html',
  styleUrl: './medication-form.component.scss',
})
export class MedicationFormComponent implements OnInit {
  isEdit = false;
  isSaving = false;
  medicationId?: number;

  private fb = inject(FormBuilder);
  private medicationService = inject(MedicationService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  form = this.fb.nonNullable.group({
    category: ['', Validators.required],
    code: ['', Validators.required],
    material_name: ['', Validators.required],
    physical_stock: [0, [Validators.required, Validators.min(0)]],
    months_of_supply: [0, [Validators.required, Validators.min(0)]],
  });

  ngOnInit() {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.isEdit = true;
      this.medicationId = Number(idParam);
      this.medicationService.get(this.medicationId).subscribe((medication) => {
        this.form.patchValue(medication);
      });
    }
  }

  submit() {
    if (this.form.invalid || this.isSaving) {
      this.form.markAllAsTouched();
      return;
    }
    this.isSaving = true;
    const payload = this.form.getRawValue();

    const request = this.isEdit && this.medicationId
      ? this.medicationService.update(this.medicationId, payload)
      : this.medicationService.create(payload);

    request.subscribe({
      next: () => {
        this.isSaving = false;
        this.router.navigate(['/medications']);
      },
      error: () => {
        this.isSaving = false;
      },
    });
  }
}
