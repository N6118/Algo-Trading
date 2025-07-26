import { AxiosError } from 'axios';

export type ServiceError = {
  message: string;
  code?: string;
  details?: any;
};

export type ServiceResult<T> = {
  data: T | null;
  error: ServiceError | null;
  isLoading: boolean;
};

export const createServiceResult = <T>(): ServiceResult<T> => ({
  data: null,
  error: null,
  isLoading: false,
});

export const handleServiceError = (error: unknown): ServiceError => {
  if (error instanceof Error) {
    return {
      message: error.message,
      code: error.name === 'AxiosError' ? (error as AxiosError).response?.status?.toString() : undefined,
      details: error.name === 'AxiosError' ? (error as AxiosError).response?.data : undefined,
    };
  }
  return {
    message: 'An unexpected error occurred',
  };
};

export function createServiceWrapper<T, Args extends any[]>(
  serviceFn: (...args: Args) => Promise<T>
): (...args: Args) => Promise<ServiceResult<T>> {
  return async (...args: Args) => {
    const result = createServiceResult<T>();
    result.isLoading = true;
    
    try {
      const data = await serviceFn(...args);
      result.data = data;
      result.error = null;
    } catch (error) {
      result.error = handleServiceError(error);
      result.data = null;
    } finally {
      result.isLoading = false;
    }
    
    return result;
  };
}
