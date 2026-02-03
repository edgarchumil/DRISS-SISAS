import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';

import { AuthService } from '../core/auth.service';
import { MovementService } from '../core/movement.service';
import { Movement } from '../shared/models';

interface MovementRow {
  id: number;
  type: 'ingreso' | 'egreso';
  medication: string;
  quantity: number;
  municipality: string;
  user: string;
  date: string;
  time: string;
  notes: string;
}

@Component({
  selector: 'app-audit',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './audit.component.html',
  styleUrl: './audit.component.scss',
})
export class AuditComponent implements OnInit {
  movements: MovementRow[] = [];
  paginated: MovementRow[] = [];
  isLoading = false;
  currentPage = 1;
  pageSize = 15;
  totalPages = 1;

  private movementService = inject(MovementService);
  private authService = inject(AuthService);
  private router = inject(Router);

  ngOnInit() {
    this.loadMovements();
  }

  loadMovements() {
    this.isLoading = true;
    this.movementService.list().subscribe({
      next: (response) => {
        this.movements = response.results.map((item) => this.mapMovement(item));
        this.currentPage = 1;
        this.updatePagination();
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
      },
    });
  }

  changePage(delta: number) {
    const nextPage = this.currentPage + delta;
    if (nextPage < 1 || nextPage > this.totalPages) {
      return;
    }
    this.currentPage = nextPage;
    this.updatePagination();
  }

  private updatePagination() {
    this.totalPages = Math.max(1, Math.ceil(this.movements.length / this.pageSize));
    const start = (this.currentPage - 1) * this.pageSize;
    const end = start + this.pageSize;
    this.paginated = this.movements.slice(start, end);
  }

  private mapMovement(movement: Movement): MovementRow {
    const created = new Date(movement.created_at);
    const datePart = created.toLocaleDateString('es-GB');
    const time = created.toLocaleTimeString('es-GB', { hour12: false });
    return {
      id: movement.id,
      type: movement.type,
      medication: movement.medication_name,
      quantity: movement.quantity,
      municipality: movement.municipality_name || '-',
      user: movement.user_name || '-',
      date: datePart,
      time,
      notes: movement.notes || '-',
    };
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
